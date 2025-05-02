import re
from typing import Dict, List, Tuple, Optional, Any, Union

def identify_db_operation_intent(query: str) -> str:
    """
    识别用户查询中的数据库操作意图
    
    Args:
        query: 用户的原始查询
        
    Returns:
        operation_intent: 操作意图 ("create", "read", "update", "delete" 或 "none")
    """
    # 创建/添加操作的关键词
    create_keywords = ["添加", "新增", "创建", "增加", "录入", "加入", "建立"]
    # 更新/修改操作的关键词
    update_keywords = ["更新", "修改", "变更", "改变", "编辑", "更改"]
    # 删除操作的关键词
    delete_keywords = ["删除", "移除", "去掉", "清除"]
    # 查询操作的关键词
    read_keywords = ["查询", "查找", "搜索", "了解", "获取", "显示", "告诉我"]
    
    # 检查是否包含创建关键词
    if any(keyword in query for keyword in create_keywords):
        return "create"
    
    # 检查是否包含更新关键词
    elif any(keyword in query for keyword in update_keywords):
        return "update"
    
    # 检查是否包含删除关键词
    elif any(keyword in query for keyword in delete_keywords):
        return "delete"
    
    # 检查是否包含查询关键词
    elif any(keyword in query for keyword in read_keywords):
        return "read"
    
    # 默认为无操作意图
    else:
        return "none"

def extract_entity_from_query(query: str, entity_types: List[str]) -> Dict[str, str]:
    """
    从查询中提取实体
    
    Args:
        query: 用户的原始查询
        entity_types: 要提取的实体类型列表
        
    Returns:
        entities: 提取的实体字典 {实体类型: 实体值}
    """
    entities = {}
    
    # 药品名称的正则表达式模式
    # drug_patterns = [
    #     r"(?:药品|药物|药)\s*(?:叫|名称为|是|:|：)\s*['\"]?([^\"'\s]+)['\"]?",
    #     r"['\"]([^\"']+)['\"]\s*(?:这个|这种|的)\s*(?:药品|药物|药)",
    #     r"(?:添加|修改|删除|查询)\s*([^\s]+)\s*(?:这个|这种|的)?\s*(?:药品|药物|药)"
    # ]

    symptom_patterns = [
        r"(?:增加|添加|删除|查询)?(?:症状|病人|药品)?([^\s，、。]+)",
    ]

    symptom_change_patterns = r"(?:把|将)(?:症状|病人|药品)([\w\u4e00-\u9fa5]+)修改(?:成|为)([\w\u4e00-\u9fa5]+)"
    
    # 属性的正则表达式模式
    attribute_patterns = {
        "副作用": [r"副作用\s*[是为:：]\s*([^，。；\n]+)", r"([^，。；\n]+)\s*的?副作用"],
        "禁忌症": [r"禁忌症\s*[是为:：]\s*([^，。；\n]+)", r"([^，。；\n]+)\s*的?禁忌症"],
        "相互作用": [r"相互作用\s*[是为:：]\s*([^，。；\n]+)", r"([^，。；\n]+)\s*的?相互作用"],
        "用法用量": [r"用法用量\s*[是为:：]\s*([^，。；\n]+)", r"([^，。；\n]+)\s*的?用法用量"]
    }
    
    # 提取药品名称
    # if "药品" in entity_types:
    #     for pattern in drug_patterns:
    #         matches = re.findall(pattern, query)
    #         if matches:
    #             entities["药品"] = matches[0].strip()
    #             break
    
    # 提取属性
    for attr_type, patterns in attribute_patterns.items():
        if attr_type in entity_types:
            for pattern in patterns:
                matches = re.findall(pattern, query)
                if matches:
                    entities[attr_type] = matches[0].strip()
                    break
    
    # 提取实体信息
    for enti in entity_types:
        if query.find("修改") != -1:
            match = re.search(symptom_change_patterns, query)
            if match:
                old_symptom = match.group(1)
                new_symptom = match.group(2)
                entities["名称"] = old_symptom.strip()
                entities[enti] = new_symptom.strip()
                return entities
    
        for pattern in symptom_patterns:
            matches = re.findall(pattern, query)
            if matches:
                entities[enti] = matches[0].strip()
                return entities

    print(entities)
    return entities

def generate_db_operation_prompt(operation_intent: str, entities: Dict[str, str]) -> str:
    """
    生成数据库操作的提示信息
    
    Args:
        operation_intent: 操作意图
        entities: 提取的实体字典
        
    Returns:
        prompt: 数据库操作的提示信息
    """
    if operation_intent == "none" or not entities:
        return "我无法理解您想要进行的数据库操作。请明确指出您想要添加、修改、删除或查询的内容。"
    
    drug_name = entities.get("药品", "未指定药品")
    
    if operation_intent == "create":
        attributes = ", ".join([f"{k}: {v}" for k, v in entities.items() if k != "药品"])
        if attributes:
            return f"您想要添加药品 '{drug_name}' 的以下属性: {attributes}。请确认是否正确？"
        else:
            return f"您想要添加药品 '{drug_name}'，但未指定任何属性。请提供药品的属性信息，如副作用、禁忌症等。"
    
    elif operation_intent == "read":
        attributes = ", ".join([k for k in entities.keys() if k != "药品"]) or "所有信息"
        return f"您想要查询药品 '{drug_name}' 的 {attributes}。请稍等，我正在查询数据库..."
    
    elif operation_intent == "update":
        attributes = ", ".join([f"{k}: {v}" for k, v in entities.items() if k != "药品"])
        if attributes:
            return f"您想要修改药品 '{drug_name}' 的以下属性: {attributes}。请确认是否正确？"
        else:
            return f"您想要修改药品 '{drug_name}'，但未指定要修改的属性。请提供要修改的属性信息，如副作用、禁忌症等。"
    
    elif operation_intent == "delete":
        attributes = ", ".join([k for k in entities.keys() if k != "药品"]) or "所有信息"
        return f"您想要删除药品 '{drug_name}' 的 {attributes}。请确认是否正确？这将永久删除相关数据。"
    
    return "我无法理解您想要进行的数据库操作。请明确指出您想要添加、修改、删除或查询的内容。"