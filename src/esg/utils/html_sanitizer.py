"""HTML净化工具

提供XSS防护的HTML标签和属性净化功能。
"""

import re
from typing import List, Set


class HTMLSanitizer:
    """HTML净化器

    用于清理用户输入，防止XSS攻击。
    只允许白名单内的标签和属性。
    """

    # 允许的标签白名单
    ALLOWED_TAGS: Set[str] = {
        "p",
        "br",
        "strong",
        "b",
        "em",
        "i",
        "u",
        "span",
        "div",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "ul",
        "ol",
        "li",
        "a",
        "img",
        "table",
        "thead",
        "tbody",
        "tr",
        "td",
        "th",
        "code",
        "pre",
        "blockquote",
    }

    # 安全：危险标签列表 - 这些标签会被完全移除（而不仅仅是转义）
    DANGEROUS_TAGS: Set[str] = {
        "script",
        "style",
        "iframe",
        "frame",
        "frameset",
        "object",
        "embed",
        "applet",
        "meta",
        "link",
        "base",
        "form",
        "input",
        "textarea",
        "button",
        "select",
        "option",
        "optgroup",
        "svg",
        "math",
        "noscript",
        "template",
        "slot",
        "canvas",
        "portal",
    }

    # 允许的属性白名单（按标签）
    ALLOWED_ATTRIBUTES: dict = {
        "a": {"href", "title", "target"},
        "img": {"src", "alt", "title", "width", "height"},
        "span": {"style"},
        "div": {"style"},
        "p": {"style"},
        "td": {"style", "colspan", "rowspan"},
        "th": {"style", "colspan", "rowspan"},
        "table": {"style"},
    }

    # 允许的CSS样式属性
    ALLOWED_STYLES: Set[str] = {
        "color",
        "background-color",
        "font-size",
        "font-weight",
        "text-align",
        "text-decoration",
        "padding",
        "margin",
        "border",
        "border-radius",
        "display",
        "width",
        "height",
        "opacity",
        "font-style",
    }

    # 危险的URL协议
    DANGEROUS_PROTOCOLS: Set[str] = {
        "javascript:",
        "vbscript:",
        "data:",
        "mhtml:",
        "file:",
        "about:",
        "blob:",
    }

    # 安全：事件属性前缀列表 - 这些属性会被移除
    EVENT_ATTRIBUTES: Set[str] = {
        "onclick",
        "ondblclick",
        "onmousedown",
        "onmouseup",
        "onmouseover",
        "onmousemove",
        "onmouseout",
        "onmouseenter",
        "onmouseleave",
        "onkeydown",
        "onkeypress",
        "onkeyup",
        "onfocus",
        "onblur",
        "onchange",
        "onsubmit",
        "onreset",
        "onselect",
        "onload",
        "onunload",
        "onerror",
        "onresize",
        "onscroll",
        "oncontextmenu",
        "onbeforeunload",
        "onbeforeprint",
        "onafterprint",
        "onhashchange",
        "onpageshow",
        "onpagehide",
        "onpopstate",
        "onstorage",
        "ononline",
        "onoffline",
        "ondrag",
        "ondragstart",
        "ondragend",
        "ondragenter",
        "ondragleave",
        "ondragover",
        "ondrop",
        "oncopy",
        "oncut",
        "onpaste",
        "ontouchstart",
        "ontouchmove",
        "ontouchend",
        "ontouchcancel",
    }

    @classmethod
    def sanitize(cls, html: str) -> str:
        """净化HTML字符串

        Args:
            html: 原始HTML字符串

        Returns:
            净化后的安全HTML字符串
        """
        if not html:
            return ""

        # 第一步：处理注释
        html = cls._remove_comments(html)

        # 第二步：处理标签
        html = cls._sanitize_tags(html)

        # 第三步：处理剩余的特殊字符
        html = cls._escape_special_chars(html)

        return html

    @classmethod
    def _remove_comments(cls, html: str) -> str:
        """移除HTML注释"""
        return re.sub(r"<!--.*?-->", "", html, flags=re.DOTALL)

    @classmethod
    def _sanitize_tags(cls, html: str) -> str:
        """净化标签"""
        # 匹配所有标签（包括自闭合和带命名空间的标签）
        pattern = r"<(/?)([a-zA-Z][a-zA-Z0-9]*)([^>]*)>"

        def replace_tag(match):
            """替换单个标签的匹配结果

            处理HTML标签匹配，根据标签类型决定保留、移除或转义。

            Args:
                match: 正则表达式匹配对象，包含标签的分组信息

            Returns:
                处理后的标签字符串，或空字符串（危险标签），或转义后的文本（非白名单标签）
            """
            # 边界条件检查：确保match对象有效
            if not match or match.group(0) is None:
                return ""

            slash = match.group(1) if match.group(1) else ""
            tag_name = match.group(2).lower() if match.group(2) else ""
            attributes = match.group(3) if match.group(3) else ""

            # 边界条件检查：确保标签名有效
            if not tag_name:
                return cls._escape_html(match.group(0))

            # 安全：检查是否是危险标签（如script），直接移除
            if tag_name in cls.DANGEROUS_TAGS:
                return ""  # 完全移除危险标签及其内容

            # 检查标签是否在白名单中
            if tag_name not in cls.ALLOWED_TAGS:
                # 对不在白名单中的标签进行转义
                return cls._escape_html(match.group(0))

            # 净化属性
            clean_attrs = cls._sanitize_attributes(tag_name, attributes)

            return f"<{slash}{tag_name}{clean_attrs}>"

        # 首先处理script/style等危险标签的内容（使用非贪婪匹配）
        for dangerous_tag in cls.DANGEROUS_TAGS:
            # 匹配完整的标签对及其内容
            content_pattern = re.compile(
                rf"<{dangerous_tag}\b[^>]*>.*?</{dangerous_tag}\s*>", re.DOTALL | re.IGNORECASE
            )
            html = content_pattern.sub("", html)
            # 匹配自闭合的危险标签
            self_closing_pattern = re.compile(rf"<{dangerous_tag}\b[^>]*/?>", re.IGNORECASE)
            html = self_closing_pattern.sub("", html)

        return re.sub(pattern, replace_tag, html)

    @classmethod
    def _sanitize_attributes(cls, tag_name: str, attributes: str) -> str:
        """净化属性"""
        allowed_attrs = cls.ALLOWED_ATTRIBUTES.get(tag_name, set())
        clean_attrs = []

        # 匹配所有属性（支持引号包裹和无引号的值）
        pattern = r'([a-zA-Z][a-zA-Z0-9\-]*)(?:\s*=\s*(?:"([^"]*)"|\'([^\']*)\'|([^\s>]*)))?'
        matches = re.findall(pattern, attributes)

        for match in matches:
            attr_name = match[0].lower()
            # 获取属性值（三种匹配组的任意一个）
            attr_value = match[1] or match[2] or match[3] or ""

            # 安全：检查是否是事件属性（如onclick），直接跳过
            if attr_name in cls.EVENT_ATTRIBUTES or attr_name.startswith("on"):
                continue

            if attr_name not in allowed_attrs:
                continue

            # 处理style属性
            if attr_name == "style":
                attr_value = cls._sanitize_style(attr_value)
                if not attr_value:
                    continue

            # 处理URL属性（href, src）
            if attr_name in {"href", "src"}:
                attr_value = cls._sanitize_url(attr_value)
                if not attr_value:
                    continue

            # 转义属性值中的引号
            attr_value = attr_value.replace('"', '"').replace("'", "&#x27;")

            clean_attrs.append(f' {attr_name}="{attr_value}"')

        return "".join(clean_attrs)

    @classmethod
    def _sanitize_style(cls, style: str) -> str:
        """净化CSS样式"""
        if not style:
            return ""

        clean_styles = []

        # 分离样式声明
        declarations = style.split(";")

        for declaration in declarations:
            declaration = declaration.strip()
            if ":" not in declaration:
                continue

            prop, value = declaration.split(":", 1)
            prop = prop.strip().lower()
            value = value.strip()

            # 检查属性是否在白名单中
            if prop not in cls.ALLOWED_STYLES:
                continue

            # 检查值中是否包含危险内容
            if cls._contains_dangerous_content(value):
                continue

            clean_styles.append(f"{prop}: {value}")

        return "; ".join(clean_styles)

    @classmethod
    def _sanitize_url(cls, url: str) -> str:
        """净化URL"""
        if not url:
            return ""

        url = url.strip()
        url_lower = url.lower()

        # 安全：检查危险协议（移除空白字符后检查，防止绕过）
        # 处理如 "java\nscript:" 或 "java\tscript:" 等绕过手段
        normalized_url = "".join(url_lower.split())

        for protocol in cls.DANGEROUS_PROTOCOLS:
            if normalized_url.startswith(protocol):
                return ""

        # 安全：额外的javascript协议检查（处理编码绕过）
        # 检查URL解码后的内容
        import urllib.parse

        try:
            decoded_url = urllib.parse.unquote(normalized_url)
            if decoded_url.startswith("javascript:") or "javascript:" in decoded_url:
                return ""
        except Exception:
            pass

        # 允许http/https/mailto/tel
        allowed_protocols = ("http://", "https://", "mailto:", "tel:")
        if not any(url_lower.startswith(p) for p in allowed_protocols) and not url_lower.startswith(
            "#"
        ):
            # 如果不以允许的协议开头，也不是相对URL，则添加https://
            if not url_lower.startswith("/") and not url_lower.startswith("./"):
                url = "https://" + url

        return url

    @classmethod
    def _contains_dangerous_content(cls, value: str) -> bool:
        """检查是否包含危险内容"""
        value = value.lower()

        # 检查JavaScript表达式
        dangerous_patterns = [
            "javascript:",
            "expression(",
            "url(",
            "@import",
            "behavior:",
            "-moz-binding",
        ]

        return any(pattern in value for pattern in dangerous_patterns)

    @classmethod
    def _escape_html(cls, text: str) -> str:
        """转义HTML特殊字符"""
        # 安全：注意转义顺序，必须先转义&，否则其他转义后的&会被再次转义
        return (
            text.replace("&", "&")  # 首先转义&
            .replace("<", "<")  # 然后转义<
            .replace(">", ">")  # 然后转义>
            .replace('"', '"')  # 转义双引号
            .replace("'", "&#x27;")
        )  # 转义单引号

    @classmethod
    def _escape_special_chars(cls, html: str) -> str:
        """处理剩余的特殊字符"""
        # 处理未闭合的<和>符号
        html = re.sub(r"<(?![\w/])", "<", html)
        html = re.sub(r'(?<![\w"\'])>', ">", html)

        return html

    @classmethod
    def sanitize_for_markdown(cls, text: str) -> str:
        """为Markdown净化文本（更严格的模式）"""
        if not text:
            return ""

        # 移除所有HTML标签
        text = re.sub(r"<[^>]+>", "", text)

        # 转义Markdown特殊字符
        text = (
            text.replace("\\", "\\\\")
            .replace("*", "\\*")
            .replace("_", "\\_")
            .replace("`", "\\`")
            .replace("[", "\\[")
            .replace("]", "\\]")
        )

        return text


def sanitize_html(html: str) -> str:
    """便捷的HTML净化函数"""
    return HTMLSanitizer.sanitize(html)


def sanitize_for_markdown(text: str) -> str:
    """便捷的Markdown净化函数"""
    return HTMLSanitizer.sanitize_for_markdown(text)
