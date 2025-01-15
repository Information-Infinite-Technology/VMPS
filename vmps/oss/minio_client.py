from minio import Minio

# 配置 MinIO 客户端
minio_client = Minio(
    "127.0.0.1:9000",  # MinIO 地址
    access_key="H7qm0nkiXJsOoinpfOtK",  # 替换为你的 Access Key
    secret_key="g2GWbM4UDwOM9JbJNYvfZjywtYOo4EoYUzX7wEAN",  # 替换为你的 Secret Key
    secure=False  # 如果使用 HTTPS，则设置为 True
)

# 检查或创建存储桶
bucket_name = "infoconnect"
