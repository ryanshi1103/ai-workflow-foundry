"""Mock data generator with 30+ example items covering all required scenarios.

All data is explicitly marked as fictional. No real personal information is used.
"""

# ruff: noqa: E501 — mock data strings naturally exceed line length

# fmt: off
MOCK_DATA = [
    # === Chinese (中文) ===
    # 1. 严重负面 - 产品质量
    {"platform": "电商平台", "source_type": "mock", "external_id": "mock-001",
     "author_display_name": "小明", "language": "zh",
     "content": "买了这个XX手机，用了不到一个月电池就完全充不进去了，质量问题太严重了！找客服也没人理。",
     "brand": "示例电子", "product": "XX手机", "search_keyword": "电池"},
    # 2. 负面 - 服务态度
    {"platform": "微博", "source_type": "mock", "external_id": "mock-002",
     "author_display_name": "愤怒的用户", "language": "zh",
     "content": "客服直接挂了我电话，态度特别差，等了半小时就这待遇？",
     "brand": "示例电商", "product": "客服服务", "search_keyword": "客服"},
    # 3. 负面 - 安全投诉（严重）
    {"platform": "论坛", "source_type": "mock", "external_id": "mock-003",
     "author_display_name": "security_concern", "language": "zh",
     "content": "我的账号被异地登录了，订单信息全被看到了，这是数据泄露吧？平台安全措施太差了。",
     "brand": "示例平台", "product": "账号安全", "search_keyword": "数据泄露"},
    # 4. 负面 - 退款问题
    {"platform": "微博", "source_type": "mock", "external_id": "mock-004",
     "author_display_name": "等退款的人", "language": "zh",
     "content": "申请退款已经两周了还没收到钱，客服一直说在处理中，这效率真让人无语。",
     "brand": "示例电商", "product": "退款", "search_keyword": "退款"},
    # 5. 正面评价
    {"platform": "小红书", "source_type": "mock", "external_id": "mock-005",
     "author_display_name": " happy_customer", "language": "zh",
     "content": "这个产品真心不错，推荐给大家！做工精细，用起来很顺手。",
     "brand": "示例电子", "product": "XX产品", "search_keyword": ""},
    # 6. 中性问题
    {"platform": "知乎", "source_type": "mock", "external_id": "mock-006",
     "author_display_name": "求知者", "language": "zh",
     "content": "请问这个型号支持蓝牙连接吗？我想买但不确定功能是否满足需求。",
     "brand": "示例电子", "product": "XX型号", "search_keyword": "蓝牙"},
    # 7. 反讽
    {"platform": "微博", "source_type": "mock", "external_id": "mock-007",
     "author_display_name": "幽默大师", "language": "zh",
     "content": "太棒了，这手机用了三天就坏了，真是好质量呢 👍",
     "brand": "示例电子", "product": "XX手机", "search_keyword": ""},
    # 8. 广告/垃圾内容
    {"platform": "微博", "source_type": "mock", "external_id": "mock-008",
     "author_display_name": "促销达人", "language": "zh",
     "content": "限时优惠！！！全场5折起，点击链接购买 https://example.com/deal",
     "brand": "", "product": "", "search_keyword": ""},
    # 9. 混合评价
    {"platform": "电商平台", "source_type": "mock", "external_id": "mock-009",
     "author_display_name": "理性消费者", "language": "zh",
     "content": "产品整体不错，物流也快，就是包装有点简陋，盒子都压扁了。希望下次改进。",
     "brand": "示例电子", "product": "XX产品", "search_keyword": "包装"},
    # 10. 普通产品建议
    {"platform": "论坛", "source_type": "mock", "external_id": "mock-010",
     "author_display_name": "热心用户", "language": "zh",
     "content": "建议增加深色模式，晚上用太刺眼了。功能本身挺好的，就是这个细节需要优化。",
     "brand": "示例软件", "product": "XX应用", "search_keyword": "深色模式"},
    # 11. 负面 - 配送问题
    {"platform": "外卖平台", "source_type": "mock", "external_id": "mock-011",
     "author_display_name": "饿了的顾客", "language": "zh",
     "content": "外卖送了两个小时还没到，饭都凉透了，配送员态度还不好。",
     "brand": "示例外卖", "product": "配送", "search_keyword": "配送"},
    # 12. 负面 - 价格投诉
    {"platform": "电商平台", "source_type": "mock", "external_id": "mock-012",
     "author_display_name": "price_watcher", "language": "zh",
     "content": "刚买完就降价200块，联系客服说不支持价格保护，太坑了。",
     "brand": "示例电商", "product": "价格", "search_keyword": "降价"},
    # 13. 负面 - 隐私担忧
    {"platform": "论坛", "source_type": "mock", "external_id": "mock-013",
     "author_display_name": "privacy_first", "language": "zh",
     "content": "这个App为什么要读取我的通讯录？根本没有必要的权限要求。",
     "brand": "示例应用", "product": "隐私", "search_keyword": "隐私"},
    # 14. 中性 - 引用别人的差评
    {"platform": "知乎", "source_type": "mock", "external_id": "mock-014",
     "author_display_name": "围观群众", "language": "zh",
     "content": "看到有人说这个产品质量很差，我还没买，想问问大家是真的吗？",
     "brand": "示例电子", "product": "XX产品", "search_keyword": ""},
    # 15. 正面中带小缺点
    {"platform": "小红书", "source_type": "mock", "external_id": "mock-015",
     "author_display_name": "mostly_happy", "language": "zh",
     "content": "超级好用！就是价格稍微贵了一点，但值得这个价。",
     "brand": "示例电子", "product": "XX产品", "search_keyword": ""},
    # === English ===
    # 16. Severe negative - product quality
    {"platform": "Twitter", "source_type": "mock", "external_id": "mock-016",
     "author_display_name": "@angry_customer", "language": "en",
     "content": "This is the worst laptop I've ever bought. Screen flickers constantly and the fan sounds like a jet engine. Total waste of money.",
     "brand": "ExampleTech", "product": "Laptop X", "search_keyword": "screen"},
    # 17. Negative - service
    {"platform": "Reddit", "source_type": "mock", "external_id": "mock-017",
     "author_display_name": "u/frustrated_user", "language": "en",
     "content": "Customer support told me they'd call back in 24 hours. It's been 5 days and nothing. Absolutely terrible service.",
     "brand": "ExampleTelco", "product": "Support", "search_keyword": "support"},
    # 18. Severe - security
    {"platform": "Twitter", "source_type": "mock", "external_id": "mock-018",
     "author_display_name": "@security_alert", "language": "en",
     "content": "Just found out my account was accessed from another country. All my payment info is saved there. This is a serious security breach!",
     "brand": "ExampleBank", "product": "Account", "search_keyword": "security breach"},
    # 19. Positive
    {"platform": "Instagram", "source_type": "mock", "external_id": "mock-019",
     "author_display_name": "@happy_user", "language": "en",
     "content": "Love this app! It's made my workflow so much smoother. Highly recommend to everyone in my team.",
     "brand": "ExampleApp", "product": "App Pro", "search_keyword": ""},
    # 20. Neutral question
    {"platform": "Reddit", "source_type": "mock", "external_id": "mock-020",
     "author_display_name": "u/new_user_123", "language": "en",
     "content": "Does anyone know if this software supports exporting to PDF? I can't find it in the documentation.",
     "brand": "ExampleApp", "product": "App Pro", "search_keyword": "PDF export"},
    # 21. Sarcasm
    {"platform": "Twitter", "source_type": "mock", "external_id": "mock-021",
     "author_display_name": "@sarcastic_techie", "language": "en",
     "content": "Oh great, another update that breaks everything. Just what I needed on a Monday morning. Fantastic work dev team!",
     "brand": "ExampleApp", "product": "App Pro", "search_keyword": "update"},
    # 22. Spam/ad
    {"platform": "Twitter", "source_type": "mock", "external_id": "mock-022",
     "author_display_name": "@deal_bot", "language": "en",
     "content": "BUY NOW!!! 80% OFF all products! Limited time offer! Click here: https://spam.example.com",
     "brand": "", "product": "", "search_keyword": ""},
    # 23. Mixed review
    {"platform": "Amazon", "source_type": "mock", "external_id": "mock-023",
     "author_display_name": "balanced_reviewer", "language": "en",
     "content": "The sound quality is amazing but the battery life is disappointing. I get maybe 3 hours on a full charge. Good for home use but not for travel.",
     "brand": "ExampleAudio", "product": "Headphones Pro", "search_keyword": "battery"},
    # 24. Product suggestion
    {"platform": "Reddit", "source_type": "mock", "external_id": "mock-024",
     "author_display_name": "u/feature_requester", "language": "en",
     "content": "Would be great if you could add keyboard shortcuts for common actions. The current menu-based workflow is a bit slow.",
     "brand": "ExampleApp", "product": "App Pro", "search_keyword": "keyboard"},
    # 25. Delivery complaint
    {"platform": "Amazon", "source_type": "mock", "external_id": "mock-025",
     "author_display_name": "waiting_customer", "language": "en",
     "content": "Package was supposed to arrive yesterday. Tracking hasn't updated in 3 days. Where is my order?",
     "brand": "ExampleStore", "product": "Delivery", "search_keyword": "delivery"},
    # 26. News reporting (not personal complaint)
    {"platform": "Twitter", "source_type": "mock", "external_id": "mock-026",
     "author_display_name": "@tech_news", "language": "en",
     "content": "Breaking: ExampleTech facing class-action lawsuit over defective batteries in their latest smartphone model. Shares down 5%.",
     "brand": "ExampleTech", "product": "Smartphone", "search_keyword": "lawsuit"},
    # 27. Unrelated insult
    {"platform": "Twitter", "source_type": "mock", "external_id": "mock-027",
     "author_display_name": "@troll_account", "language": "en",
     "content": "You guys are idiots! Nobody cares about your stupid product! Get a real job!",
     "brand": "ExampleTech", "product": "", "search_keyword": ""},
    # 28. Low confidence - ambiguous
    {"platform": "Reddit", "source_type": "mock", "external_id": "mock-028",
     "author_display_name": "u/confused_user", "language": "en",
     "content": "Not sure if it's just me or if the app is actually slower after the update. Anyone else?",
     "brand": "ExampleApp", "product": "App Pro", "search_keyword": "update"},
    # 29. Negative - misinformation
    {"platform": "Facebook", "source_type": "mock", "external_id": "mock-029",
     "author_display_name": "share_everything", "language": "en",
     "content": "I heard this company is using child labor in their factories! Everyone should boycott them! Share this!",
     "brand": "ExampleBrand", "product": "", "search_keyword": "boycott"},
    # 30. Performance complaint
    {"platform": "App Store", "source_type": "mock", "external_id": "mock-030",
     "author_display_name": "slow_app_user", "language": "en",
     "content": "This app crashes every time I try to open a large file. Been like this for 3 versions now. Fix it please.",
     "brand": "ExampleApp", "product": "App Pro", "search_keyword": "crash"},
    # 31. Duplicate-like content (similar but not identical)
    {"platform": "电商平台", "source_type": "mock", "external_id": "mock-031",
     "author_display_name": "重复测试", "language": "zh",
     "content": "电池问题，用了不到一个月电池就出问题了，质量不好。",
     "brand": "示例电子", "product": "XX手机", "search_keyword": "电池"},
    # 32. 负面 - 账号问题
    {"platform": "微博", "source_type": "mock", "external_id": "mock-032",
     "author_display_name": "locked_out", "language": "zh",
     "content": "账号莫名其妙被封了，申诉了一个月也没人处理，里面的余额怎么办？",
     "brand": "示例平台", "product": "账号", "search_keyword": "封号"},
    # 33. 负面 - 性能问题
    {"platform": "论坛", "source_type": "mock", "external_id": "mock-033",
     "author_display_name": "tech_user", "language": "zh",
     "content": "更新到最新版本后卡得要死，打开一个页面要等10秒，这是反向优化吗？",
     "brand": "示例软件", "product": "XX应用", "search_keyword": "卡顿"},
    # 34. 正面 - 英文
    {"platform": "Twitter", "source_type": "mock", "external_id": "mock-034",
     "author_display_name": "@real_fan", "language": "en",
     "content": "Best purchase of the year! The customer service team went above and beyond to help me set everything up.",
     "brand": "ExampleTech", "product": "Device Z", "search_keyword": ""},
    # 35. 负面 - 广告虚假宣传
    {"platform": "电商平台", "source_type": "mock", "external_id": "mock-035",
     "author_display_name": "受骗消费者", "language": "zh",
     "content": "实物和宣传图完全不一样，颜色差了十万八千里，这不算虚假宣传吗？",
     "brand": "示例服饰", "product": "XX外套", "search_keyword": "虚假宣传"},
    # === Expanded: more problem_feedback items ===
    # 36. 问题反馈 - 隐私问题
    {"platform": "论坛", "source_type": "mock", "external_id": "mock-036",
     "author_display_name": "privacy_advocate", "language": "zh",
     "content": "这个App在后台偷偷上传我的位置信息，即使我关掉了定位权限。这是侵犯隐私吧？",
     "brand": "示例应用", "product": "隐私设置", "search_keyword": "隐私"},
    # 37. 问题反馈 - 政策争议
    {"platform": "微博", "source_type": "mock", "external_id": "mock-037",
     "author_display_name": "policy_watcher", "language": "zh",
     "content": "新版的用户协议简直就是霸王条款，把所有责任都推给用户，平台自己没有责任。",
     "brand": "示例平台", "product": "用户协议", "search_keyword": "政策"},
    # 38. 问题反馈 - 安全问题（英文）
    {"platform": "Reddit", "source_type": "mock", "external_id": "mock-038",
     "author_display_name": "u/safety_first", "language": "en",
     "content": "The product overheated and started smoking while charging. This is a serious fire hazard! Someone could get hurt.",
     "brand": "ExampleTech", "product": "Charger X", "search_keyword": "safety hazard"},
    # 39. 问题反馈 - 配送损坏
    {"platform": "电商平台", "source_type": "mock", "external_id": "mock-039",
     "author_display_name": "失望买家", "language": "zh",
     "content": "收到货的时候外包装全是湿的，打开一看里面的产品也泡坏了，这么贵的东西就这么废了。",
     "brand": "示例电子", "product": "XX设备", "search_keyword": "损坏"},
    # 40. 问题反馈 - 退款纠纷（英文）
    {"platform": "Amazon", "source_type": "mock", "external_id": "mock-040",
     "author_display_name": "refund_seeker", "language": "en",
     "content": "I returned the item three weeks ago and they confirmed receipt, but still haven't issued my refund. This is unacceptable.",
     "brand": "ExampleStore", "product": "Returns", "search_keyword": "refund"},
    # === Expanded: more experience_feedback items ===
    # 41. 体验反馈 - 表扬客服
    {"platform": "小红书", "source_type": "mock", "external_id": "mock-041",
     "author_display_name": "感恩用户", "language": "zh",
     "content": "客服小张真的太棒了！耐心解答了我所有问题，还帮我申请了优惠。这样的服务太让人感动了！",
     "brand": "示例电商", "product": "客服", "search_keyword": "表扬"},
    # 42. 体验反馈 - 功能需求
    {"platform": "论坛", "source_type": "mock", "external_id": "mock-042",
     "author_display_name": "power_user", "language": "zh",
     "content": "希望能增加批量导出功能和自定义报表，现在手动一条条导出太慢了。",
     "brand": "示例软件", "product": "XX应用", "search_keyword": "批量导出"},
    # 43. 体验反馈 - 推荐（英文）
    {"platform": "Twitter", "source_type": "mock", "external_id": "mock-043",
     "author_display_name": "@recommendations", "language": "en",
     "content": "Been using this for 6 months now and it just keeps getting better. The recent update finally added the features I wanted. Highly recommend!",
     "brand": "ExampleApp", "product": "App Pro", "search_keyword": ""},
    # 44. 体验反馈 - 中性讨论
    {"platform": "知乎", "source_type": "mock", "external_id": "mock-044",
     "author_display_name": "理性讨论者", "language": "zh",
     "content": "客观来说这个产品在同类中算中上水平，功能齐全但UI设计略显过时，看个人需求吧。",
     "brand": "示例软件", "product": "XX应用", "search_keyword": "讨论"},
    # 45. 体验反馈 - 改进建议
    {"platform": "Reddit", "source_type": "mock", "external_id": "mock-045",
     "author_display_name": "u/ux_designer", "language": "en",
     "content": "The onboarding flow is confusing for new users. I'd suggest adding a guided tutorial and simplifying the first-run experience.",
     "brand": "ExampleApp", "product": "App Pro", "search_keyword": "onboarding"},
    # 46. 体验反馈 - 正面评价（简短）
    {"platform": "App Store", "source_type": "mock", "external_id": "mock-046",
     "author_display_name": "happy_user_2024", "language": "en",
     "content": "Simple, effective, exactly what I needed. Five stars!",
     "brand": "ExampleApp", "product": "App Pro", "search_keyword": ""},
    # 47. 体验反馈 - 混合感受
    {"platform": "电商平台", "source_type": "mock", "external_id": "mock-047",
     "author_display_name": "中等评价", "language": "zh",
     "content": "物流慢了一天，但客服很快帮我查了进度还给了补偿券，整体体验还行吧。",
     "brand": "示例电商", "product": "配送服务", "search_keyword": "物流"},
    # 48. 问题反馈 - 产品质量（英文详细）
    {"platform": "Reddit", "source_type": "mock", "external_id": "mock-048",
     "author_display_name": "u/detailed_review", "language": "en",
     "content": "After 2 weeks of use, the keyboard started double-typing keys and the trackpad became unresponsive. Manufacturing quality has clearly declined compared to the previous model.",
     "brand": "ExampleTech", "product": "Laptop X", "search_keyword": "keyboard"},
    # 49. 体验反馈 - 表扬产品功能
    {"platform": "微博", "source_type": "mock", "external_id": "mock-049",
     "author_display_name": "科技爱好者", "language": "zh",
     "content": "这次更新的AI功能太强大了！工作效率直接翻倍，不得不给开发团队点赞。",
     "brand": "示例软件", "product": "XX应用", "search_keyword": "AI"},
    # 50. 完全无关内容
    {"platform": "微博", "source_type": "mock", "external_id": "mock-050",
     "author_display_name": "random_user", "language": "zh",
     "content": "今天天气真好，适合出去郊游。有没有人一起去爬山？",
     "brand": "", "product": "", "search_keyword": ""},
]
# fmt: on
