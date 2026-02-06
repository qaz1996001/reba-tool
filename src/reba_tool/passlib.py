from passlib.hash import pbkdf2_sha256

# 你的原始密碼
password = "qaz1996001"

# 你的哈希值
hashed_password = "pbkdf2_sha256$870000$ard9loNNTm9dhaKax9q64p$rXP/pUlqk+QdY52JB1wr3CMZ+DayhIugtFUKm0FTVAA="

# 驗證密碼
if pbkdf2_sha256.verify(password, hashed_password):
    print("密碼正確！")
else:
    print("密碼錯誤！")
