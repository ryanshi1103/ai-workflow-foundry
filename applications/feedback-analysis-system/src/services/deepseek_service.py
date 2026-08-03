"""DeepSeek API service with retry, timeout, caching, and mock mode."""

import hashlib
import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from openai import OpenAI
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from src.config import (
    APP_MOCK_MODE,
    DEEPSEEK_API_KEY,
    DEEPSEEK_BASE_URL,
    DEEPSEEK_MAX_CONCURRENCY,
    DEEPSEEK_MAX_CONTENT_LENGTH,
    DEEPSEEK_MODEL,
    DEEPSEEK_THINKING,
    DEEPSEEK_TIMEOUT_SECONDS,
)
from src.prompts.sentiment_v1 import SYSTEM_PROMPT, USER_MESSAGE_TEMPLATE
from src.schemas import DeepSeekAnalysisResult

logger = logging.getLogger(__name__)

# Simple in-memory cache for analysis results
_analysis_cache: dict[str, DeepSeekAnalysisResult] = {}

# Mock responses for demo mode
_MOCK_RESPONSES = [
    {  # 0: problem_feedback - product quality
        "is_relevant": True,
        "feedback_type": "problem_feedback",
        "sentiment": "negative",
        "sentiment_score": -0.82,
        "is_negative": True,
        "complaint_category": "product_quality",
        "complaint_subcategory": "battery_failure",
        "target": "示例产品",
        "severity": 78,
        "urgency": "high",
        "requires_action": True,
        "action_priority": "high",
        "confidence": 0.91,
        "summary": "用户投诉产品电池在短期使用后失效",
        "evidence": "用了不到一个月电池就完全充不进去了",
        "suggested_action": "联系用户核实批次并检查同型号投诉",
        "needs_human_review": False,
    },
    {  # 1: problem_feedback - service complaint
        "is_relevant": True,
        "feedback_type": "problem_feedback",
        "sentiment": "negative",
        "sentiment_score": -0.65,
        "is_negative": True,
        "complaint_category": "service_attitude",
        "complaint_subcategory": "rude_staff",
        "target": "客服部门",
        "severity": 55,
        "urgency": "medium",
        "requires_action": True,
        "action_priority": "medium",
        "confidence": 0.85,
        "summary": "用户投诉客服态度恶劣",
        "evidence": "客服直接挂了我电话，态度特别差",
        "suggested_action": "调取通话录音核实，对相关客服进行培训",
        "needs_human_review": False,
    },
    {  # 2: problem_feedback - security (critical)
        "is_relevant": True,
        "feedback_type": "problem_feedback",
        "sentiment": "negative",
        "sentiment_score": -0.90,
        "is_negative": True,
        "complaint_category": "security",
        "complaint_subcategory": "data_leak",
        "target": "用户数据",
        "severity": 92,
        "urgency": "critical",
        "requires_action": True,
        "action_priority": "critical",
        "confidence": 0.88,
        "summary": "用户报告个人数据疑似泄露",
        "evidence": "我的账号被异地登录，订单信息全被看到了",
        "suggested_action": "立即启动安全事件响应流程，通知数据保护团队",
        "needs_human_review": True,
    },
    {  # 3: problem_feedback - refund
        "is_relevant": True,
        "feedback_type": "problem_feedback",
        "sentiment": "negative",
        "sentiment_score": -0.55,
        "is_negative": True,
        "complaint_category": "refund",
        "complaint_subcategory": "delayed_refund",
        "target": "退款流程",
        "severity": 40,
        "urgency": "medium",
        "requires_action": True,
        "action_priority": "medium",
        "confidence": 0.78,
        "summary": "用户投诉退款迟迟未到账",
        "evidence": "申请退款已经两周了还没收到钱",
        "suggested_action": "查询退款进度，联系支付渠道确认",
        "needs_human_review": False,
    },
    {  # 4: experience_feedback - positive
        "is_relevant": True,
        "feedback_type": "experience_feedback",
        "sentiment": "positive",
        "sentiment_score": 0.85,
        "is_negative": False,
        "complaint_category": "none",
        "complaint_subcategory": "",
        "target": "",
        "severity": 0,
        "urgency": "low",
        "requires_action": False,
        "action_priority": "low",
        "confidence": 0.95,
        "summary": "用户给出了积极评价",
        "evidence": "这个产品真心不错，推荐给大家",
        "suggested_action": "",
        "needs_human_review": False,
    },
    {  # 5: experience_feedback - neutral question
        "is_relevant": True,
        "feedback_type": "experience_feedback",
        "sentiment": "neutral",
        "sentiment_score": 0.05,
        "is_negative": False,
        "complaint_category": "none",
        "complaint_subcategory": "",
        "target": "",
        "severity": 5,
        "urgency": "low",
        "requires_action": False,
        "action_priority": "low",
        "confidence": 0.90,
        "summary": "用户提出中性问题咨询",
        "evidence": "请问这个型号支持蓝牙连接吗",
        "suggested_action": "",
        "needs_human_review": False,
    },
    {  # 6: experience_feedback - needs human review (possible sarcasm)
        "is_relevant": True,
        "feedback_type": "experience_feedback",
        "sentiment": "negative",
        "sentiment_score": -0.20,
        "is_negative": False,
        "complaint_category": "none",
        "complaint_subcategory": "",
        "target": "",
        "severity": 10,
        "urgency": "low",
        "requires_action": False,
        "action_priority": "low",
        "confidence": 0.40,
        "summary": "可能是反讽，置信度低",
        "evidence": "太棒了，这手机用了三天就坏了，真是好质量呢",
        "suggested_action": "需要人工判断是否为反讽",
        "needs_human_review": True,
    },
    {  # 7: not relevant - ad/spam
        "is_relevant": False,
        "feedback_type": "unknown",
        "sentiment": "unknown",
        "sentiment_score": 0.0,
        "is_negative": False,
        "complaint_category": "none",
        "complaint_subcategory": "",
        "target": "",
        "severity": 0,
        "urgency": "low",
        "requires_action": False,
        "action_priority": "low",
        "confidence": 0.95,
        "summary": "检测为广告或垃圾内容",
        "evidence": "限时优惠！！！全场5折起，点击链接购买",
        "suggested_action": "",
        "needs_human_review": False,
    },
    {  # 8: problem_feedback - delivery
        "is_relevant": True,
        "feedback_type": "problem_feedback",
        "sentiment": "negative",
        "sentiment_score": -0.70,
        "is_negative": True,
        "complaint_category": "delivery",
        "complaint_subcategory": "late_delivery",
        "target": "配送服务",
        "severity": 45,
        "urgency": "medium",
        "requires_action": True,
        "action_priority": "medium",
        "confidence": 0.87,
        "summary": "用户投诉外卖配送严重延误",
        "evidence": "外卖送了两个小时还没到，饭都凉透了",
        "suggested_action": "联系配送团队核实延误原因并补偿用户",
        "needs_human_review": False,
    },
    {  # 9: problem_feedback - account
        "is_relevant": True,
        "feedback_type": "problem_feedback",
        "sentiment": "negative",
        "sentiment_score": -0.75,
        "is_negative": True,
        "complaint_category": "account",
        "complaint_subcategory": "account_locked",
        "target": "账号系统",
        "severity": 68,
        "urgency": "high",
        "requires_action": True,
        "action_priority": "high",
        "confidence": 0.86,
        "summary": "用户账号被锁定，申诉未得到处理",
        "evidence": "账号莫名其妙被封了，申诉了一个月也没人处理",
        "suggested_action": "核查账号状态并联系用户处理",
        "needs_human_review": False,
    },
    {  # 10: experience_feedback - suggestion/feature request
        "is_relevant": True,
        "feedback_type": "experience_feedback",
        "sentiment": "neutral",
        "sentiment_score": 0.10,
        "is_negative": False,
        "complaint_category": "none",
        "complaint_subcategory": "",
        "target": "",
        "severity": 5,
        "urgency": "low",
        "requires_action": False,
        "action_priority": "low",
        "confidence": 0.89,
        "summary": "用户提出产品改进建议",
        "evidence": "建议增加深色模式，晚上用太刺眼了",
        "suggested_action": "将建议加入产品需求池评估",
        "needs_human_review": False,
    },
    {  # 11: experience_feedback - mixed review
        "is_relevant": True,
        "feedback_type": "experience_feedback",
        "sentiment": "mixed",
        "sentiment_score": 0.15,
        "is_negative": False,
        "complaint_category": "other",
        "complaint_subcategory": "packaging",
        "target": "产品包装",
        "severity": 15,
        "urgency": "low",
        "requires_action": False,
        "action_priority": "low",
        "confidence": 0.83,
        "summary": "产品整体满意但包装需要改进",
        "evidence": "产品整体不错，物流也快，就是包装有点简陋",
        "suggested_action": "",
        "needs_human_review": False,
    },
    {  # 12: problem_feedback - price dispute
        "is_relevant": True,
        "feedback_type": "problem_feedback",
        "sentiment": "negative",
        "sentiment_score": -0.60,
        "is_negative": True,
        "complaint_category": "price",
        "complaint_subcategory": "price_drop_after_purchase",
        "target": "价格保护政策",
        "severity": 35,
        "urgency": "low",
        "requires_action": True,
        "action_priority": "low",
        "confidence": 0.82,
        "summary": "用户投诉购买后立即降价，不支持价保",
        "evidence": "刚买完就降价200块，联系客服说不支持价格保护",
        "suggested_action": "核实价保政策并考虑给予补偿",
        "needs_human_review": False,
    },
    {  # 13: problem_feedback - false advertising
        "is_relevant": True,
        "feedback_type": "problem_feedback",
        "sentiment": "negative",
        "sentiment_score": -0.72,
        "is_negative": True,
        "complaint_category": "advertising",
        "complaint_subcategory": "product_mismatch",
        "target": "商品宣传",
        "severity": 58,
        "urgency": "high",
        "requires_action": True,
        "action_priority": "high",
        "confidence": 0.84,
        "summary": "用户投诉实物与宣传严重不符",
        "evidence": "实物和宣传图完全不一样，颜色差了十万八千里",
        "suggested_action": "核实商品描述准确性，联系用户处理退换",
        "needs_human_review": False,
    },
    {  # 14: experience_feedback - praise with minor note
        "is_relevant": True,
        "feedback_type": "experience_feedback",
        "sentiment": "positive",
        "sentiment_score": 0.72,
        "is_negative": False,
        "complaint_category": "none",
        "complaint_subcategory": "",
        "target": "",
        "severity": 3,
        "urgency": "low",
        "requires_action": False,
        "action_priority": "low",
        "confidence": 0.92,
        "summary": "用户对产品给出高度正面评价",
        "evidence": "超级好用！就是价格稍微贵了一点，但值得这个价。",
        "suggested_action": "",
        "needs_human_review": False,
    },
    {  # 15: not relevant - news reporting
        "is_relevant": False,
        "feedback_type": "unknown",
        "sentiment": "neutral",
        "sentiment_score": 0.0,
        "is_negative": False,
        "complaint_category": "none",
        "complaint_subcategory": "",
        "target": "",
        "severity": 0,
        "urgency": "low",
        "requires_action": False,
        "action_priority": "low",
        "confidence": 0.93,
        "summary": "新闻转述，非个人投诉",
        "evidence": "Breaking: ExampleTech facing class-action lawsuit over defective batteries",
        "suggested_action": "",
        "needs_human_review": False,
    },
]


def _get_cache_key(content: str, model: str) -> str:
    raw = f"{content}|{model}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class DeepSeekService:
    """Service for analyzing feedback content with DeepSeek API."""

    def __init__(self):
        self._client: OpenAI | None = None
        self._mock_index = 0

    @property
    def client(self) -> OpenAI | None:
        if self._client is None and DEEPSEEK_API_KEY:
            self._client = OpenAI(
                api_key=DEEPSEEK_API_KEY,
                base_url=DEEPSEEK_BASE_URL,
                timeout=DEEPSEEK_TIMEOUT_SECONDS,
            )
        return self._client

    @property
    def mock_mode(self) -> bool:
        return APP_MOCK_MODE or not DEEPSEEK_API_KEY

    def _get_mock_response(self, content: str) -> DeepSeekAnalysisResult:
        """Return a deterministic mock response based on content characteristics."""
        # Simple heuristic to pick a mock response based on content
        content_lower = content.lower()

        if any(w in content_lower for w in ["广告", "ad", "spam", "buy now", "click here", "限时", "促销"]):
            return DeepSeekAnalysisResult(**_MOCK_RESPONSES[7])
        if any(w in content_lower for w in ["安全", "security", "泄露", "hack", "密码", "password", "breach"]):
            return DeepSeekAnalysisResult(**_MOCK_RESPONSES[2])
        if any(w in content_lower for w in ["退款", "refund", "退货", "退钱"]):
            return DeepSeekAnalysisResult(**_MOCK_RESPONSES[3])
        if any(w in content_lower for w in ["客服", "态度", "rude", "service", "服务员", "support"]):
            if any(w in content_lower for w in ["挂", "差", "rude", "terrible", "无语"]):
                return DeepSeekAnalysisResult(**_MOCK_RESPONSES[1])
            return DeepSeekAnalysisResult(**_MOCK_RESPONSES[4])
        if any(w in content_lower for w in ["电池", "坏", "坏了", "broken", "fail", "battery", "screen flicker"]):
            return DeepSeekAnalysisResult(**_MOCK_RESPONSES[0])
        if any(w in content_lower for w in ["太棒了", "sarcasm", "真是好", "反讽"]) or (
            "好" in content_lower and "坏" in content_lower
        ):
            return DeepSeekAnalysisResult(**_MOCK_RESPONSES[6])
        if any(w in content_lower for w in ["请问", "how", "怎么", "question", "what", "anyone know"]):
            return DeepSeekAnalysisResult(**_MOCK_RESPONSES[5])
        if any(w in content_lower for w in ["建议", "建议增加", "add", "would be great", "feature", "wish", "希望"]):
            return DeepSeekAnalysisResult(**_MOCK_RESPONSES[10])
        if any(w in content_lower for w in ["好", "great", "推荐", "excellent", "love", "喜欢", "best purchase"]):
            return DeepSeekAnalysisResult(**_MOCK_RESPONSES[4])
        if any(w in content_lower for w in ["配送", "delivery", "外卖", "送", "package", "order", "tracking"]):
            return DeepSeekAnalysisResult(**_MOCK_RESPONSES[8])
        if any(w in content_lower for w in ["账号", "account", "封", "locked", "被封"]):
            return DeepSeekAnalysisResult(**_MOCK_RESPONSES[9])
        if any(w in content_lower for w in ["降价", "price", "价格", "贵"]):
            return DeepSeekAnalysisResult(**_MOCK_RESPONSES[12])
        if any(w in content_lower for w in ["虚假", "宣传", "实物和", "不一样", "misleading"]):
            return DeepSeekAnalysisResult(**_MOCK_RESPONSES[13])
        _mixed_keywords = ["包装", "简陋", "但是", "整体不错", "可惜", "disappointing", "amazing but"]
        if any(w in content_lower for w in _mixed_keywords):
            return DeepSeekAnalysisResult(**_MOCK_RESPONSES[11])
        if any(w in content_lower for w in ["lawsuit", "facing", "class-action", "shares down", "breaking"]):
            return DeepSeekAnalysisResult(**_MOCK_RESPONSES[15])
        if any(w in content_lower for w in ["不错", "值得", "好用", "推荐", "超级"]):
            return DeepSeekAnalysisResult(**_MOCK_RESPONSES[14])

        # Default: round-robin among problem feedback types
        problem_indices = [0, 1, 3, 8, 9]
        self._mock_index = (self._mock_index + 1) % len(problem_indices)
        return DeepSeekAnalysisResult(**_MOCK_RESPONSES[problem_indices[self._mock_index]])

    @retry(
        retry=retry_if_exception_type(Exception),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        reraise=True,
    )
    def _call_deepseek_api(self, content: str, platform: str = "", author: str = "",
                           published_at: str = "", engagement_count: str = "",
                           brand: str = "", product: str = "") -> DeepSeekAnalysisResult:
        """Call DeepSeek API with retry logic."""

        if len(content) > DEEPSEEK_MAX_CONTENT_LENGTH:
            content = content[:DEEPSEEK_MAX_CONTENT_LENGTH]

        # Check cache
        cache_key = _get_cache_key(content, DEEPSEEK_MODEL)
        if cache_key in _analysis_cache:
            logger.info("Cache hit for content hash=%s", cache_key[:16])
            return _analysis_cache[cache_key]

        # Mock mode
        if self.mock_mode:
            result = self._get_mock_response(content)
            _analysis_cache[cache_key] = result
            return result

        client = self.client
        if client is None:
            raise RuntimeError("DeepSeek API key not configured and mock mode is off")

        user_message = USER_MESSAGE_TEMPLATE.format(
            platform=platform,
            author=author or "unknown",
            published_at=published_at or "unknown",
            engagement_count=engagement_count or "0",
            brand=brand or "N/A",
            product=product or "N/A",
            content=content,
        )

        extra_body: dict[str, Any] = {}
        if not DEEPSEEK_THINKING:
            extra_body["thinking"] = {"type": "disabled"}

        start_time = time.time()
        try:
            response = client.chat.completions.create(
                model=DEEPSEEK_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
                extra_body=extra_body if extra_body else None,
            )

            elapsed = time.time() - start_time
            raw_json = response.choices[0].message.content or "{}"

            # Record usage
            usage = response.usage
            input_tokens = usage.prompt_tokens if usage else None
            output_tokens = usage.completion_tokens if usage else None

            logger.info(
                "DeepSeek API call: %.2fs, in=%s, out=%s",
                elapsed,
                input_tokens,
                output_tokens,
            )

            # Parse and validate JSON
            result = self._parse_response(raw_json)
            _analysis_cache[cache_key] = result
            return result

        except Exception as e:
            elapsed = time.time() - start_time
            logger.error("DeepSeek API error after %.2fs: %s", elapsed, e)
            raise

    def _parse_response(self, raw_json: str) -> DeepSeekAnalysisResult:
        """Parse and validate the JSON response from DeepSeek."""
        try:
            data = json.loads(raw_json)
        except json.JSONDecodeError as e:
            logger.error("Failed to parse DeepSeek JSON response: %s", e)
            raise ValueError(f"DeepSeek returned invalid JSON: {e}") from e

        # Ensure required fields have defaults
        defaults = {
            "feedback_type": "unknown",
            "sentiment": "unknown",
            "complaint_category": "none",
            "urgency": "low",
            "action_priority": "low",
            "complaint_subcategory": "",
            "target": "",
            "summary": "",
            "evidence": "",
            "suggested_action": "",
        }
        for field, default in defaults.items():
            if field not in data or data[field] is None:
                data[field] = default

        # Coerce booleans
        for bool_field in ("is_relevant", "is_negative", "requires_action", "needs_human_review"):
            if bool_field in data and not isinstance(data[bool_field], bool):
                data[bool_field] = bool(data[bool_field])

        # Coerce severity
        try:
            data["severity"] = max(0, min(100, int(data.get("severity", 0))))
        except (ValueError, TypeError):
            data["severity"] = 0

        # Coerce sentiment_score
        try:
            data["sentiment_score"] = max(-1.0, min(1.0, float(data.get("sentiment_score", 0.0))))
        except (ValueError, TypeError):
            data["sentiment_score"] = 0.0

        # Coerce confidence
        try:
            data["confidence"] = max(0.0, min(1.0, float(data.get("confidence", 0.5))))
        except (ValueError, TypeError):
            data["confidence"] = 0.5

        return DeepSeekAnalysisResult(**data)

    def analyze_single(self, content: str, platform: str = "", author: str = "",
                       published_at: str = "", engagement_count: str = "",
                       brand: str = "", product: str = "") -> DeepSeekAnalysisResult:
        """Analyze a single piece of content."""
        return self._call_deepseek_api(
            content=content,
            platform=platform,
            author=author,
            published_at=published_at,
            engagement_count=engagement_count,
            brand=brand,
            product=product,
        )

    def analyze_batch(
        self,
        items: list[dict[str, Any]],
        max_concurrency: int | None = None,
        on_progress: Any = None,
    ) -> list[tuple[int, DeepSeekAnalysisResult | None, str | None]]:
        """Analyze multiple items concurrently.

        Args:
            items: List of dicts with keys matching FeedbackItem fields
            max_concurrency: Max parallel API calls
            on_progress: Optional callback(current, total)

        Returns:
            List of (index, result_or_none, error_message_or_none)
        """
        concurrency = max_concurrency or DEEPSEEK_MAX_CONCURRENCY
        results: list[tuple[int, DeepSeekAnalysisResult | None, str | None]] = []

        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            future_to_idx = {}
            for idx, item in enumerate(items):
                future = executor.submit(
                    self._call_deepseek_api,
                    content=item.get("content", ""),
                    platform=item.get("platform", ""),
                    author=item.get("author_display_name", ""),
                    published_at=str(item.get("published_at", "")),
                    engagement_count=str(item.get("engagement_count", "0")),
                    brand=item.get("brand", ""),
                    product=item.get("product", ""),
                )
                future_to_idx[future] = idx

            total = len(items)
            for completed, future in enumerate(as_completed(future_to_idx), start=1):
                idx = future_to_idx[future]
                try:
                    result = future.result(timeout=DEEPSEEK_TIMEOUT_SECONDS + 30)
                    results.append((idx, result, None))
                except Exception as e:
                    logger.error("Analysis failed for item %d: %s", idx, e)
                    results.append((idx, None, str(e)))
                if on_progress:
                    on_progress(completed, total)

        return sorted(results, key=lambda x: x[0])

    def clear_cache(self):
        """Clear the analysis cache."""
        _analysis_cache.clear()


# Singleton
deepseek_service = DeepSeekService()
