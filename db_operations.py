import py2neo
import re
from typing import Dict, List, Tuple, Optional, Any, Union

class Neo4jOperations:
    """处理Neo4j数据库的增删改查操作"""
    
    def __init__(self, uri='bolt:http://localhost:7474', user='neo4j', password='123456789', name='neo4j'):
        """初始化Neo4j数据库连接"""
        self.client = py2neo.Graph(uri, user=user, password=password, name=name)
    
    def parse_db_operation_intent(self, query: str, entities: Dict) -> Tuple[str, Dict]:
        """解析用户的数据库操作意图
        
        Args:
            query: 用户的原始查询
            entities: 识别出的实体字典
            
        Returns:
            operation_type: 操作类型 (create, read, update, delete)
            operation_details: 操作详情字典
        """
        # 默认为查询操作
        operation_type = "read"
        operation_details = {}
        
        # 创建/添加操作的关键词
        create_keywords = ["添加", "新增", "创建", "增加", "录入", "加入", "建立"]
        # 更新/修改操作的关键词
        update_keywords = ["更新", "修改", "变更", "改变", "编辑"]
        # 删除操作的关键词
        delete_keywords = ["删除", "移除", "去掉", "清除"]
        
        # 检查是否包含创建关键词
        if any(keyword in query for keyword in create_keywords):
            operation_type = "create"
            # 提取要创建的节点类型和属性
            operation_details["node_type"] = self._extract_node_type(query, entities)
            operation_details["properties"] = self._extract_properties(query, entities)
        
        # 检查是否包含更新关键词
        elif any(keyword in query for keyword in update_keywords):
            operation_type = "update"
            # 提取要更新的节点类型、标识和属性
            operation_details["node_type"] = self._extract_node_type(query, entities)
            operation_details["node_id"] = self._extract_node_id(query, entities)
            operation_details["properties"] = self._extract_properties(query, entities)
        
        # 检查是否包含删除关键词
        elif any(keyword in query for keyword in delete_keywords):
            operation_type = "delete"
            # 提取要删除的节点类型和标识
            operation_details["node_type"] = self._extract_node_type(query, entities)
            operation_details["node_id"] = self._extract_node_id(query, entities)
        
        # 默认为查询操作
        else:
            operation_type = "read"
            # 提取要查询的节点类型和条件
            operation_details["node_type"] = self._extract_node_type(query, entities)
            operation_details["conditions"] = self._extract_conditions(query, entities)
        
        return operation_type, operation_details
    
    def _extract_node_type(self, query: str, entities: Dict) -> str:
        """从查询和实体中提取节点类型"""
        # 常见节点类型映射
        node_types = {
            "疾病": "疾病",
            "药品": "药品",
            "食物": "食物",
            "检查": "检查项目",
            "检查项目": "检查项目",
            "症状": "疾病症状",
            "科目": "科目",
            "药品商": "药品商",
            "治疗方法": "治疗方法"
        }
        
        # 首先从实体中提取
        for entity_type, entity_value in entities.items():
            if entity_type in node_types:
                return node_types[entity_type]
        
        # 如果实体中没有，从查询中提取
        for node_key, node_type in node_types.items():
            if node_key in query:
                return node_type
        
        # 默认返回疾病类型
        return "疾病"
    
    def _extract_node_id(self, query: str, entities: Dict) -> str:
        """从查询和实体中提取节点标识（通常是名称）"""
        # 从实体中提取
        node_type = self._extract_node_type(query, entities)
        
        # 根据节点类型从实体中获取对应的值
        entity_mapping = {
            "疾病": "疾病",
            "药品": "药品",
            "食物": "食物",
            "检查项目": "检查项目",
            "疾病症状": "疾病症状",
            "科目": "科目",
            "药品商": "药品商",
            "治疗方法": "治疗方法"
        }
        
        for entity_type, entity_value in entities.items():
            if entity_type in entity_mapping and entity_mapping[entity_type] == node_type:
                return entity_value
        
        # 如果实体中没有，尝试从查询中提取
        # 这里使用简单的正则表达式，实际应用中可能需要更复杂的NLP技术
        patterns = [
            r"(?:名为|叫做|名称是|叫|名称为)\s*['\"]?([^\"']+)['\"]?",
            r"['\"]([^\"']+)['\"]\s*(?:的|这个|这种)",
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, query)
            if matches:
                return matches[0]
        
        return ""
    
    def _extract_properties(self, query: str, entities: Dict) -> Dict:
        """从查询中提取属性键值对"""
        properties = {}
        
        # 常见属性模式
        # 例如："将感冒的症状改为发热、咳嗽"
        # 或者："添加一个名为阿司匹林的药品，其副作用是胃出血"
        property_patterns = [
            # 属性名:属性值 模式
            r"([\w\u4e00-\u9fa5]+)\s*[:：]\s*([\w\u4e00-\u9fa5、，,]+)",
            # 将X改为Y模式
            r"将\s*([\w\u4e00-\u9fa5]+)\s*(?:改为|修改为|变更为|更新为)\s*([\w\u4e00-\u9fa5、，,]+)",
            # 的X是Y模式
            r"的\s*([\w\u4e00-\u9fa5]+)\s*是\s*([\w\u4e00-\u9fa5、，,]+)",
        ]
        
        for pattern in property_patterns:
            matches = re.findall(pattern, query)
            for prop_name, prop_value in matches:
                # 清理属性名和值
                prop_name = prop_name.strip()
                prop_value = prop_value.strip()
                
                # 常见属性名映射
                prop_name_mapping = {
                    "症状": "疾病的症状",
                    "病因": "疾病病因",
                    "简介": "疾病简介",
                    "预防": "预防措施",
                    "治疗": "治疗的方法",
                    "周期": "治疗周期",
                    "概率": "治愈概率",
                    "人群": "疾病易感人群",
                    "药品": "疾病使用药品",
                    "宜吃": "疾病宜吃食物",
                    "忌吃": "疾病忌吃食物",
                    "检查": "疾病所需检查",
                    "科目": "疾病所属科目",
                    "并发": "疾病并发疾病",
                    "副作用": "副作用",
                    "禁忌症": "禁忌症",
                    "相互作用": "相互作用",
                    "用法用量": "用法用量",
                    "生产商": "生产商"
                }
                
                # 映射属性名
                for key, value in prop_name_mapping.items():
                    if key in prop_name:
                        prop_name = value
                        break
                
                properties[prop_name] = prop_value
        
        return properties
    
    def _extract_conditions(self, query: str, entities: Dict) -> Dict:
        """从查询中提取查询条件"""
        conditions = {}
        
        # 从实体中提取条件
        for entity_type, entity_value in entities.items():
            if entity_type in ["疾病", "药品", "食物", "检查项目", "疾病症状", "科目", "药品商", "治疗方法"]:
                conditions["名称"] = entity_value
        
        return conditions
    
    def execute_operation(self, operation_type: str, operation_details: Dict) -> Tuple[bool, str, Any]:
        """执行数据库操作
        
        Args:
            operation_type: 操作类型 (create, read, update, delete)
            operation_details: 操作详情字典
            
        Returns:
            success: 操作是否成功
            message: 操作结果消息
            data: 操作返回的数据（如果有）
        """
        try:
            if operation_type == "create":
                return self._create_node(operation_details)
            elif operation_type == "read":
                return self._read_node(operation_details)
            elif operation_type == "update":
                return self._update_node(operation_details)
            elif operation_type == "delete":
                return self._delete_node(operation_details)
            else:
                return False, f"不支持的操作类型: {operation_type}", None
        except Exception as e:
            return False, f"执行数据库操作时出错: {str(e)}", None
    
    def _create_node(self, details: Dict) -> Tuple[bool, str, Any]:
        """创建节点"""
        node_type = details.get("node_type", "")
        properties = details.get("properties", {})
        
        # print(details)
        # 确保有节点类型和至少有名称属性
        if not node_type or "名称" not in properties:
            return False, "创建节点需要指定节点类型和名称", None
        
        # 检查节点是否已存在
        check_query = f"MATCH (n:{node_type} {{名称: $name}}) RETURN n"
        result = self.client.run(check_query, name=properties["名称"]).data()
        print("检查节点：", check_query)
        
        if result:
            return False, f"节点已存在: {node_type} - {properties['名称']}", None
        
        # 构建创建节点的Cypher查询
        props_str = ", ".join([f"{k}: ${k}" for k in properties.keys()])
        create_query = f"CREATE (n:{node_type} {{{props_str}}}) RETURN n"
        
        # 执行查询
        result = self.client.run(create_query, **properties).data()
        
        if result:
            return True, f"成功创建节点: {node_type} - {properties['名称']}", result[0]["n"]
        else:
            return False, f"创建节点失败: {node_type} - {properties['名称']}", None
    
    def _read_node(self, details: Dict) -> Tuple[bool, str, Any]:
        """查询节点"""
        node_type = details.get("node_type", "")
        conditions = details.get("conditions", {})
        
        # 确保有节点类型
        if not node_type:
            return False, "查询节点需要指定节点类型", None
        
        # 构建查询条件
        if conditions:
            conditions_str = " AND ".join([f"n.{k} = ${k}" for k in conditions.keys()])
            query = f"MATCH (n:{node_type}) WHERE {conditions_str} RETURN n"
        else:
            query = f"MATCH (n:{node_type}) RETURN n LIMIT 10"
        
        # 执行查询
        result = self.client.run(query, **conditions).data()
        
        if result:
            return True, f"查询成功，找到 {len(result)} 个节点", result
        else:
            return False, f"未找到符合条件的节点: {node_type}", None
    
    def _update_node(self, details: Dict) -> Tuple[bool, str, Any]:
        """更新节点"""
        node_type = details.get("node_type", "")
        # node_id = details.get("node_id", "")
        properties = details.get("properties", {})
        conditions = details.get("conditions", {})
        
        # 确保有节点类型和标识
        if not node_type or '名称' not in properties:
            return False, "更新节点需要指定节点类型和标识", None

        id_name = properties.get("名称", "")
        old_name = conditions.get("名称", "")

        # 检查节点是否存在
        check_query = f"MATCH (n:{node_type} {{名称: $name}}) RETURN n"
        result = self.client.run(check_query, name=old_name).data()
        
        if not result:
            return False, f"节点不存在: {node_type} - {old_name}", None
        
        # 构建更新节点的Cypher查询
        set_clauses = [f"n.{k} = ${k}" for k in properties.keys()]
        if set_clauses:
            set_str = ", ".join(set_clauses)
            update_query = f"MATCH (n:{node_type} {{名称: $name}}) SET {set_str} RETURN n"

            print("更新节点：", update_query)
            
            # 执行查询
            params = {"name": old_name, **properties}
            result = self.client.run(update_query, **params).data()
            
            if result:
                return True, f"成功更新节点: {node_type} - {old_name}", result[0]["n"]
            else:
                return False, f"更新节点失败: {node_type} - {old_name}", None
        else:
            return False, "没有指定要更新的属性", None
    
    def _delete_node(self, details: Dict) -> Tuple[bool, str, Any]:
        """删除节点"""
        node_type = details.get("node_type", "")
        # node_id = details.get("node_id", "")
        properties = details.get("properties", {})

        
        # 确保有节点类型和标识
        if not node_type or "名称" not in properties:
            return False, "删除节点需要指定节点类型和标识", None
        
        id_name = properties["名称"]

        
        # 检查节点是否存在
        check_query = f"MATCH (n:{node_type} {{名称: $name}}) RETURN n"
        result = self.client.run(check_query, name=id_name).data()
        
        if not result:
            return False, f"节点不存在: {node_type} - {id_name}", None
        
        # 先删除与该节点相关的所有关系
        delete_relations_query = f"MATCH (n:{node_type} {{名称: $name}})-[r]-() DELETE r"
        self.client.run(delete_relations_query, name=id_name)
        
        # 删除节点
        delete_query = f"MATCH (n:{node_type} {{名称: $name}}) DELETE n"
        self.client.run(delete_query, name=id_name)
        
        # 验证节点是否已删除
        verify_query = f"MATCH (n:{node_type} {{名称: $name}}) RETURN n"
        result = self.client.run(verify_query, name=id_name).data()
        
        if not result:
            return True, f"成功删除节点: {node_type} - {id_name}", None
        else:
            return False, f"删除节点失败: {node_type} - {id_name}", None
    
    def create_relationship(self, source_type: str, source_id: str, 
                           target_type: str, target_id: str, 
                           relationship_type: str) -> Tuple[bool, str, Any]:
        """创建关系"""
        # 检查源节点和目标节点是否存在
        source_query = f"MATCH (n:{source_type} {{名称: $name}}) RETURN n"
        source_result = self.client.run(source_query, name=source_id).data()
        
        target_query = f"MATCH (n:{target_type} {{名称: $name}}) RETURN n"
        target_result = self.client.run(target_query, name=target_id).data()
        
        if not source_result:
            return False, f"源节点不存在: {source_type} - {source_id}", None
        
        if not target_result:
            return False, f"目标节点不存在: {target_type} - {target_id}", None
        
        # 检查关系是否已存在
        check_rel_query = f"""MATCH (a:{source_type} {{名称: $source_id}})-[r:{relationship_type}]->
                            (b:{target_type} {{名称: $target_id}}) RETURN r"""
        rel_result = self.client.run(check_rel_query, source_id=source_id, target_id=target_id).data()
        
        if rel_result:
            return False, f"关系已存在: {source_type}({source_id}) -{relationship_type}-> {target_type}({target_id})", None
        
        # 创建关系
        create_rel_query = f"""MATCH (a:{source_type} {{名称: $source_id}}), (b:{target_type} {{名称: $target_id}})
                            CREATE (a)-[r:{relationship_type}]->(b) RETURN r"""
        result = self.client.run(create_rel_query, source_id=source_id, target_id=target_id).data()
        
        if result:
            return True, f"成功创建关系: {source_type}({source_id}) -{relationship_type}-> {target_type}({target_id})", result[0]["r"]
        else:
            return False, f"创建关系失败", None
    
    def delete_relationship(self, source_type: str, source_id: str, 
                           target_type: str, target_id: str, 
                           relationship_type: str) -> Tuple[bool, str, Any]:
        """删除关系"""
        # 检查关系是否存在
        check_rel_query = f"""MATCH (a:{source_type} {{名称: $source_id}})-[r:{relationship_type}]->
                            (b:{target_type} {{名称: $target_id}}) RETURN r"""
        rel_result = self.client.run(check_rel_query, source_id=source_id, target_id=target_id).data()
        
        if not rel_result:
            return False, f"关系不存在: {source_type}({source_id}) -{relationship_type}-> {target_type}({target_id})", None
        
        # 删除关系
        delete_rel_query = f"""MATCH (a:{source_type} {{名称: $source_id}})-[r:{relationship_type}]->
                            (b:{target_type} {{名称: $target_id}}) DELETE r"""
        self.client.run(delete_rel_query, source_id=source_id, target_id=target_id)
        
        # 验证关系是否已删除
        verify_query = f"""MATCH (a:{source_type} {{名称: $source_id}})-[r:{relationship_type}]->
                        (b:{target_type} {{名称: $target_id}}) RETURN r"""
        result = self.client.run(verify_query, source_id=source_id, target_id=target_id).data()
        
        if not result:
            return True, f"成功删除关系: {source_type}({source_id}) -{relationship_type}-> {target_type}({target_id})", None
        else:
            return False, f"删除关系失败", None
    
    def format_operation_result(self, success: bool, message: str, data: Any) -> str:
        """格式化操作结果为用户友好的消息"""
        if not success:
            return f"操作失败: {message}"
        
        if not data:
            return f"操作成功: {message}"
        
        # 格式化节点数据
        if isinstance(data, list):
            # 多个节点的情况
            result = f"操作成功: {message}\n\n查询结果:\n"
            for i, item in enumerate(data, 1):
                node = item.get("n")
                if node:
                    result += f"\n{i}. {node.get('名称', '未命名')}\n"
                    for key, value in node.items():
                        if key != "名称":
                            result += f"   - {key}: {value}\n"
            return result
        else:
            # 单个节点的情况
            if hasattr(data, "items"):
                result = f"操作成功: {message}\n\n节点详情:\n"
                result += f"名称: {data.get('名称', '未命名')}\n"
                for key, value in data.items():
                    if key != "名称":
                        result += f"{key}: {value}\n"
                return result
            else:
                return f"操作成功: {message}"