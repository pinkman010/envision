"""认证和授权模块

提供用户认证、JWT令牌管理、权限控制等功能。
"""

import functools
import hashlib
import logging
import os
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, TypeVar, Union

import jwt
import bcrypt
from cryptography.fernet import Fernet

# 配置日志
logger = logging.getLogger(__name__)

# JWT配置 - 从环境变量读取，如未设置则使用固定密钥（生产环境应使用环境变量）
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "envision-esg-secret-key-2024-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 30
JWT_REFRESH_TOKEN_EXPIRE_DAYS = 7


class Permission(Enum):
    """权限枚举"""
    VIEW_REPORTS = "view_reports"
    CREATE_REPORTS = "create_reports"
    EDIT_REPORTS = "edit_reports"
    DELETE_REPORTS = "delete_reports"
    MANAGE_USERS = "manage_users"
    MANAGE_SETTINGS = "manage_settings"
    VIEW_ANALYTICS = "view_analytics"
    EXPORT_DATA = "export_data"
    IMPORT_DATA = "import_data"
    API_ACCESS = "api_access"


class Role(Enum):
    """角色枚举"""
    ADMIN = "admin"
    ANALYST = "analyst"
    VIEWER = "viewer"
    API_USER = "api_user"


# 角色-权限映射
ROLE_PERMISSIONS: Dict[Role, Set[Permission]] = {
    Role.ADMIN: {
        Permission.VIEW_REPORTS, Permission.CREATE_REPORTS,
        Permission.EDIT_REPORTS, Permission.DELETE_REPORTS,
        Permission.MANAGE_USERS, Permission.MANAGE_SETTINGS,
        Permission.VIEW_ANALYTICS, Permission.EXPORT_DATA,
        Permission.IMPORT_DATA, Permission.API_ACCESS
    },
    Role.ANALYST: {
        Permission.VIEW_REPORTS, Permission.CREATE_REPORTS,
        Permission.EDIT_REPORTS, Permission.VIEW_ANALYTICS,
        Permission.EXPORT_DATA, Permission.API_ACCESS
    },
    Role.VIEWER: {
        Permission.VIEW_REPORTS, Permission.EXPORT_DATA
    },
    Role.API_USER: {
        Permission.API_ACCESS, Permission.VIEW_REPORTS,
        Permission.EXPORT_DATA
    }
}


@dataclass
class User:
    """用户数据类"""
    id: str
    username: str
    email: str
    role: Role
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    last_login: Optional[datetime] = None
    permissions: Set[Permission] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """初始化后设置角色权限"""
        if not self.permissions:
            self.permissions = ROLE_PERMISSIONS.get(self.role, set()).copy()
    
    def has_permission(self, permission: Permission) -> bool:
        """检查用户是否有指定权限"""
        return permission in self.permissions
    
    def has_any_permission(self, permissions: List[Permission]) -> bool:
        """检查用户是否有任一权限"""
        return any(p in self.permissions for p in permissions)
    
    def has_all_permissions(self, permissions: List[Permission]) -> bool:
        """检查用户是否有所有权限"""
        return all(p in self.permissions for p in permissions)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role.value,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'permissions': [p.value for p in self.permissions],
            'metadata': self.metadata
        }


@dataclass
class TokenData:
    """令牌数据类"""
    user_id: str
    username: str
    role: Role
    permissions: List[str]
    exp: datetime
    token_type: str = "access"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'user_id': self.user_id,
            'username': self.username,
            'role': self.role.value,
            'permissions': self.permissions,
            'exp': self.exp.isoformat(),
            'token_type': self.token_type
        }


class AuthManager:
    """认证管理器
    
    管理用户认证、令牌生成和验证。
    
    Example:
        >>> auth = AuthManager()
        >>> 
        >>> # 用户认证
        >>> user = auth.authenticate("admin", "password123")
        >>> 
        >>> # 创建令牌
        >>> token = auth.create_access_token(user)
        >>> 
        >>> # 验证令牌
        >>> token_data = auth.verify_token(token)
    """
    
    def __init__(self, secret_key: Optional[str] = None):
        """初始化认证管理器
        
        Args:
            secret_key: JWT密钥，None则自动生成
        """
        self.secret_key = secret_key or JWT_SECRET_KEY
        self._users: Dict[str, User] = {}
        self._user_credentials: Dict[str, str] = {}  # username -> hashed_password
        self._refresh_tokens: Set[str] = set()
        
        # 初始化默认用户
        self._init_default_users()
    
    def _init_default_users(self):
        """初始化默认用户"""
        # 创建默认管理员账户
        default_users = [
            {
                'id': 'admin_001',
                'username': 'admin',
                'email': 'admin@company.com',
                'role': Role.ADMIN,
                'password': 'admin123'  # 生产环境应该修改
            },
            {
                'id': 'analyst_001',
                'username': 'analyst',
                'email': 'analyst@company.com',
                'role': Role.ANALYST,
                'password': 'analyst123'
            },
            {
                'id': 'viewer_001',
                'username': 'viewer',
                'email': 'viewer@company.com',
                'role': Role.VIEWER,
                'password': 'viewer123'
            }
        ]
        
        for user_data in default_users:
            password = user_data.pop('password')
            user = User(**user_data)
            self._users[user.id] = user
            self._user_credentials[user.username] = self._hash_password(password)
    
    def _hash_password(self, password: str) -> str:
        """使用bcrypt哈希密码
        
        bcrypt自动处理盐值，提供更强的安全性。
        """
        # 生成盐并哈希密码
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """验证密码
        
        使用bcrypt验证密码，支持bcrypt哈希和旧版SHA256哈希（向后兼容）
        """
        # 检查是否是bcrypt哈希（以$2b$开头）
        if hashed_password.startswith('$2'):
            return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
        else:
            # 向后兼容：旧版SHA256哈希
            legacy_hash = hashlib.sha256(plain_password.encode()).hexdigest()
            return legacy_hash == hashed_password
    
    def authenticate(
        self,
        username: str,
        password: str
    ) -> Optional[User]:
        """用户认证
        
        Args:
            username: 用户名
            password: 密码
            
        Returns:
            认证成功返回User，失败返回None
        """
        hashed_password = self._user_credentials.get(username)
        if not hashed_password:
            logger.warning(f"认证失败：用户不存在 [{username}]")
            return None
        
        if not self._verify_password(password, hashed_password):
            logger.warning(f"认证失败：密码错误 [{username}]")
            return None
        
        # 查找用户
        user = next(
            (u for u in self._users.values() if u.username == username),
            None
        )
        
        if user and user.is_active:
            user.last_login = datetime.now()
            logger.info(f"用户认证成功 [{username}]")
            return user
        
        logger.warning(f"认证失败：用户未激活或不存在 [{username}]")
        return None
    
    def create_access_token(
        self,
        user: User,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """创建访问令牌
        
        Args:
            user: 用户对象
            expires_delta: 过期时间增量
            
        Returns:
            JWT令牌
        """
        if expires_delta is None:
            expires_delta = timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        
        expire = datetime.utcnow() + expires_delta
        
        payload = {
            'user_id': user.id,
            'username': user.username,
            'role': user.role.value,
            'permissions': [p.value for p in user.permissions],
            'exp': expire,
            'iat': datetime.utcnow(),
            'token_type': 'access'
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm=JWT_ALGORITHM)
        logger.debug(f"创建访问令牌 [{user.username}]")
        
        return token
    
    def create_refresh_token(self, user: User) -> str:
        """创建刷新令牌
        
        Args:
            user: 用户对象
            
        Returns:
            刷新令牌
        """
        expire = datetime.utcnow() + timedelta(days=JWT_REFRESH_TOKEN_EXPIRE_DAYS)
        
        payload = {
            'user_id': user.id,
            'exp': expire,
            'iat': datetime.utcnow(),
            'token_type': 'refresh'
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm=JWT_ALGORITHM)
        self._refresh_tokens.add(token)
        
        logger.debug(f"创建刷新令牌 [{user.username}]")
        return token
    
    def verify_token(self, token: str) -> Optional[TokenData]:
        """验证令牌
        
        Args:
            token: JWT令牌
            
        Returns:
            验证成功返回TokenData，失败返回None
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[JWT_ALGORITHM]
            )
            
            token_type = payload.get('token_type')
            
            if token_type == 'refresh' and token not in self._refresh_tokens:
                logger.warning("无效的刷新令牌")
                return None
            
            token_data = TokenData(
                user_id=payload['user_id'],
                username=payload['username'],
                role=Role(payload['role']),
                permissions=payload['permissions'],
                exp=datetime.fromtimestamp(payload['exp']),
                token_type=token_type
            )
            
            logger.debug(f"令牌验证成功 [{token_data.username}]")
            return token_data
            
        except jwt.ExpiredSignatureError:
            logger.warning("令牌已过期")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"无效令牌: {e}")
            return None
    
    def refresh_access_token(self, refresh_token: str) -> Optional[str]:
        """刷新访问令牌
        
        Args:
            refresh_token: 刷新令牌
            
        Returns:
            新的访问令牌或None
        """
        token_data = self.verify_token(refresh_token)
        
        if not token_data or token_data.token_type != 'refresh':
            return None
        
        # 查找用户
        user = self._users.get(token_data.user_id)
        if not user or not user.is_active:
            return None
        
        # 创建新的访问令牌
        return self.create_access_token(user)
    
    def revoke_refresh_token(self, refresh_token: str) -> bool:
        """撤销刷新令牌
        
        Args:
            refresh_token: 刷新令牌
            
        Returns:
            是否成功撤销
        """
        if refresh_token in self._refresh_tokens:
            self._refresh_tokens.discard(refresh_token)
            logger.info("刷新令牌已撤销")
            return True
        return False
    
    def create_user(
        self,
        username: str,
        email: str,
        password: str,
        role: Role = Role.VIEWER,
        **metadata
    ) -> Optional[User]:
        """创建新用户
        
        Args:
            username: 用户名
            email: 邮箱
            password: 密码
            role: 角色
            **metadata: 额外元数据
            
        Returns:
            新用户或None（如果用户名已存在）
        """
        if username in self._user_credentials:
            logger.warning(f"创建用户失败：用户名已存在 [{username}]")
            return None
        
        user_id = f"user_{len(self._users) + 1:03d}"
        
        user = User(
            id=user_id,
            username=username,
            email=email,
            role=role,
            metadata=metadata
        )
        
        self._users[user_id] = user
        self._user_credentials[username] = self._hash_password(password)
        
        logger.info(f"创建用户成功 [{username}]")
        return user
    
    def get_user(self, user_id: str) -> Optional[User]:
        """获取用户"""
        return self._users.get(user_id)
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """通过用户名获取用户"""
        return next(
            (u for u in self._users.values() if u.username == username),
            None
        )
    
    def update_user(
        self,
        user_id: str,
        **updates
    ) -> Optional[User]:
        """更新用户信息"""
        user = self._users.get(user_id)
        if not user:
            return None
        
        for key, value in updates.items():
            if hasattr(user, key):
                setattr(user, key, value)
        
        logger.info(f"更新用户成功 [{user.username}]")
        return user
    
    def delete_user(self, user_id: str) -> bool:
        """删除用户"""
        user = self._users.pop(user_id, None)
        if user:
            self._user_credentials.pop(user.username, None)
            logger.info(f"删除用户成功 [{user.username}]")
            return True
        return False
    
    def list_users(self) -> List[User]:
        """列出所有用户"""
        return list(self._users.values())


# 全局认证管理器
_global_auth_manager: Optional[AuthManager] = None


def get_auth_manager() -> AuthManager:
    """获取全局认证管理器"""
    global _global_auth_manager
    if _global_auth_manager is None:
        _global_auth_manager = AuthManager()
    return _global_auth_manager


def authenticate_user(username: str, password: str) -> Optional[User]:
    """便捷函数：用户认证"""
    return get_auth_manager().authenticate(username, password)


def create_access_token(user: User, expires_delta: Optional[timedelta] = None) -> str:
    """便捷函数：创建访问令牌"""
    return get_auth_manager().create_access_token(user, expires_delta)


def verify_token(token: str) -> Optional[TokenData]:
    """便捷函数：验证令牌"""
    return get_auth_manager().verify_token(token)


F = TypeVar('F', bound=Callable[..., Any])


def require_auth(func: F) -> F:
    """需要认证的装饰器
    
    装饰的函数第一个参数必须是token字符串。
    
    Example:
        >>> @require_auth
        ... def protected_function(token: str, data: dict):
        ...     # 只有通过认证才能执行
        ...     return process(data)
    """
    @functools.wraps(func)
    def wrapper(token: str, *args, **kwargs):
        token_data = verify_token(token)
        if not token_data:
            raise PermissionError("无效的令牌或令牌已过期")
        
        # 将token_data添加到kwargs
        return func(token, *args, token_data=token_data, **kwargs)
    
    return wrapper  # type: ignore


def require_permission(permission: Permission):
    """需要权限的装饰器
    
    Example:
        >>> @require_permission(Permission.VIEW_REPORTS)
        ... def view_reports(token: str):
        ...     # 需要有VIEW_REPORTS权限
        ...     return get_reports()
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(token: str, *args, **kwargs):
            token_data = verify_token(token)
            if not token_data:
                raise PermissionError("无效的令牌或令牌已过期")
            
            if permission.value not in token_data.permissions:
                raise PermissionError(f"缺少权限: {permission.value}")
            
            return func(token, *args, token_data=token_data, **kwargs)
        
        return wrapper  # type: ignore
    return decorator
