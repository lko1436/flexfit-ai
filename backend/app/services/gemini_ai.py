import json
from google import genai
from google.genai import types
from app.config import get_settings
from app.schemas import EatingOutCombo, MealAnalysisResponse

settings = get_settings()


class GeminiAIService:
    def __init__(self) -> None:
        self.client = genai.Client(api_key=settings.gemini_api_key) if settings.gemini_api_key else None

    def _ensure_client(self) -> genai.Client:
        if self.client is None:
            raise RuntimeError("尚未設定 GEMINI_API_KEY，請先於 backend/.env 中填入有效的 API Key。")
        return self.client

    def analyze_food_image(
        self,
        image_bytes: bytes,
        mime_type: str = "image/jpeg",
        user_hint: str | None = None,
    ) -> MealAnalysisResponse:
        """
        拍照辨識：傳入食物照片，回傳結構化熱量與三大營養素 JSON。
        """
        client = self._ensure_client()
        hint_text = f"\n使用者補充說明：{user_hint}" if user_hint else ""
        prompt = (
            "你是一位熟悉台灣外食與家常菜的專業營養師。"
            "請辨識這張照片中的食物與估算份量，並估算總熱量 (kcal)、蛋白質 (g)、碳水化合物 (g)、脂肪 (g)。"
            "若為台灣常見便當、滷味、早餐店或超商食品，請依常見份量合理估算。"
            f"{hint_text}"
        )

        response = client.models.generate_content(
            model=settings.gemini_vision_model,
            contents=[
                types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                prompt,
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=MealAnalysisResponse,
                temperature=0.2,
            ),
        )
        return MealAnalysisResponse.model_validate_json(response.text)

    def parse_food_text(self, text_description: str) -> MealAnalysisResponse:
        """
        文字快速輸入解析：例如「超商無糖豆漿一瓶 + 茶葉蛋兩顆」自動換算營養素。
        """
        client = self._ensure_client()
        prompt = (
            "你是一位熟悉台灣超商、早餐店與外食份量的營養師。"
            f"請解析以下飲食內容並估算總營養素：\n「{text_description}」"
        )

        response = client.models.generate_content(
            model=settings.gemini_vision_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=MealAnalysisResponse,
                temperature=0.2,
            ),
        )
        return MealAnalysisResponse.model_validate_json(response.text)

    def recommend_eating_out(
        self,
        remaining_kcal: int,
        remaining_protein_g: float,
        remaining_carbs_g: float,
        remaining_fat_g: float,
        scene_tag: str,
        user_saved_foods: list[dict],
        user_preference: str | None = None,
    ) -> list[EatingOutCombo]:
        """
        靈活外食推薦組合器：
        不依賴寫死菜單，直接依據當下剩餘額度、台灣外食場景，並參考使用者過去儲存的個人食物庫，
        由 AI 即時動態組合 2~3 套可執行的外食購買建議。
        """
        client = self._ensure_client()
        saved_hint = (
            f"\n【使用者個人常吃清單（可優先納入搭配）】\n{json.dumps(user_saved_foods, ensure_ascii=False)}"
            if user_saved_foods
            else "\n【使用者個人常吃清單】目前為空，請直接依台灣該場景常見真實外食單品自由組合。"
        )
        pref_text = f"\n使用者額外需求：{user_preference}" if user_preference else ""

        prompt = f"""
你是「FlexFit AI」的台灣外食飲控顧問。請絕對不要開出死板的水煮菜單，而是根據使用者目前剩餘的營養額度，
針對台灣「{scene_tag}」外食場景，即時動態組合出 **2 到 3 套** 走進店裡就買得到的真實搭配方案。

【當下剩餘額度】
- 剩餘熱量：{remaining_kcal} kcal
- 剩餘蛋白質：{remaining_protein_g:.1f} g
- 剩餘碳水：{remaining_carbs_g:.1f} g
- 剩餘脂肪：{remaining_fat_g:.1f} g
{pref_text}
{saved_hint}

請確保每個組合的總熱量貼近但不大幅超出剩餘熱量，且優先協助補足蛋白質。
"""
        response = client.models.generate_content(
            model=settings.gemini_chat_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=list[EatingOutCombo],
                temperature=0.7,
            ),
        )
        raw_list = json.loads(response.text)
        return [EatingOutCombo.model_validate(item) for item in raw_list]

    def chat_with_assistant(
        self,
        user_message: str,
        user_context: dict,
        chat_history: list[dict],
        image_bytes: bytes | None = None,
        mime_type: str = "image/jpeg",
    ) -> str:
        """
        具備記憶上下文能力的 AI 飲控小助手（支援純文字或附帶食物照片）。
        """
        client = self._ensure_client()

        system_instruction = (
            "你是「FlexFit AI（靈活飲控助手）」，語氣溫暖、像懂生活的朋友一樣務實不說教。"
            "核心理念：極低門檻、高度彈性、不強迫、善用台灣外食（7-11、全家、麥當勞、自助餐、滷味、手搖飲無糖替代）。"
            f"\n\n【使用者目前狀態】\n{json.dumps(user_context, ensure_ascii=False)}"
        )

        contents: list[types.Content] = []
        for msg in chat_history[-10:]:
            contents.append(
                types.Content(
                    role="user" if msg["role"] == "user" else "model",
                    parts=[types.Part.from_text(text=msg["content"])],
                )
            )

        current_parts: list[types.Part] = [types.Part.from_text(text=user_message)]
        if image_bytes:
            current_parts.append(types.Part.from_bytes(data=image_bytes, mime_type=mime_type))

        contents.append(types.Content(role="user", parts=current_parts))

        response = client.models.generate_content(
            model=settings.gemini_chat_model,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.6,
            ),
        )
        return response.text


gemini_service = GeminiAIService()