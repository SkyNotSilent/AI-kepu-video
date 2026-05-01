"""
模板引擎
管理关键帧动画模板
"""

import json
import logging
from typing import Dict, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class TemplateEngine:
    """模板引擎 - 管理关键帧动画模板"""
    
    def __init__(self, template_dir: str = "config/templates"):
        """
        初始化模板引擎
        
        Args:
            template_dir: 模板目录
        """
        self.template_dir = Path(template_dir)
        self.templates = {}
        
    def load(self, template_path: str) -> dict:
        """
        加载单个模板
        
        Args:
            template_path: 模板文件路径
            
        Returns:
            模板配置
        """
        path = Path(template_path)
        with open(path, 'r', encoding='utf-8') as f:
            template = json.load(f)
        
        self.templates[template["name"]] = template
        logger.info(f"加载模板: {template['name']}")
        
        return template
    
    def load_all(self):
        """加载所有模板"""
        template_files = list(self.template_dir.glob("*.json"))
        
        for file in template_files:
            self.load(file)
        
        logger.info(f"加载了 {len(self.templates)} 个模板")
    
    def get_template(self, name: str) -> Optional[dict]:
        """
        获取模板
        
        Args:
            name: 模板名称
            
        Returns:
            模板配置
        """
        return self.templates.get(name)
    
    def get_all_templates(self) -> Dict[str, dict]:
        """
        获取所有模板
        
        Returns:
            所有模板字典
        """
        return self.templates
    
    def list_templates(self) -> List[str]:
        """
        列出所有模板名称
        
        Returns:
            模板名称列表
        """
        return list(self.templates.keys())
    
    def create_template(self, name: str, template_type: str = "video") -> dict:
        """
        创建新模板
        
        Args:
            name: 模板名称
            template_type: 模板类型
            
        Returns:
            新模板配置
        """
        template = {
            "name": name,
            "type": template_type,
            "animation": {
                "intro": {
                    "type": "fade_in",
                    "duration": 1000,
                    "easing": "ease_out"
                },
                "keyframes": {}
            }
        }
        
        self.templates[name] = template
        return template
    
    def save_template(self, name: str, output_path: str):
        """
        保存模板到文件
        
        Args:
            name: 模板名称
            output_path: 输出路径
        """
        if name not in self.templates:
            raise ValueError(f"模板 {name} 不存在")
        
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.templates[name], f, indent=2, ensure_ascii=False)
        
        logger.info(f"保存模板: {name} -> {output_path}")


if __name__ == "__main__":
    # 测试代码
    engine = TemplateEngine()
    
    # 加载所有模板
    engine.load_all()
    
    # 列出所有模板
    print("可用模板:", engine.list_templates())
    
    # 获取模板
    template = engine.get_template("slide_in")
    if template:
        print("模板配置:", template)
