# Practice
Вот тебе **чистый готовый код для `README.md`**, просто вставляй как есть:

```md
# 🤖 AI-ERP System

![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-green?logo=fastapi)
![Docker](https://img.shields.io/badge/Docker-Container-blue?logo=docker)
![Status](https://img.shields.io/badge/Status-In%20Development-yellow)
![License](https://img.shields.io/badge/License-Private-lightgrey)

---

## 📌 Описание проекта

**AI-ERP System** — корпоративная ERP-система для автоматизации процессов закупок с AI-парсингом документов (PDF / Excel), ролевой системой и управлением проектами.

---

## 🚀 Возможности

- 📄 AI-парсинг PDF и Excel файлов  
- 👥 Ролевая система доступа (PM, Коммерческий директор, Бухгалтер, Завсклад)  
- 📦 Управление проектами закупок  
- 💰 Контроль счетов и оплат  
- 🔄 Workflow согласований  
- ⚙️ REST API на FastAPI  

---

## 🧠 Технологии

- Python 3.12  
- FastAPI  
- Uvicorn  
- Docker  
- PostgreSQL (в разработке)  

---

## 🏗️ Архитектура

```

Frontend (React)
↓
FastAPI Backend
↓
Business Logic Layer
↓
PostgreSQL Database
↓
AI Parsing Engine

````

---

## ⚙️ Установка и запуск

### 📥 Клонирование проекта

```bash
git clone <repo-url>
cd Ustem_group_crm
````

---

### 🐳 Запуск через Docker

```bash
docker build -t ai-erp .
docker run -p 8000:8000 ai-erp
```

---

### 💻 Локальный запуск

```bash
python -m venv venv

# Mac/Linux
source venv/bin/activate

# Windows
venv\Scripts\activate

pip install -r requirements.txt

uvicorn main:app --reload
```

---

## 📂 Структура проекта

```
Ustem_group_crm/
│
├── backend/
│   ├── main.py
│   ├── api/
│   ├── services/
│   ├── models/
│   └── utils/
│
├── Dockerfile
├── requirements.txt
└── README.md
```

---

## 👥 Роли пользователей

### 👨‍💼 Project Manager (PM)

* Создание проектов
* Загрузка документов
* Проверка AI-парсинга
* Редактирование данных

### 📊 Commercial Director

* Утверждение проектов
* Контроль маржинальности

### 💰 Accountant

* Финансовые операции
* Счета и оплаты

### 📦 Warehouse Manager

* Отгрузка товаров
* Складской учет

---

## 🔄 Workflow системы

```
Создание проекта
→ Загрузка файла
→ AI-парсинг
→ Проверка PM
→ Утверждение Комдиром
→ Бухгалтерия
→ Отгрузка
```

---

## 📡 API

```http
POST /projects/create
POST /upload/file
GET  /projects/{id}
POST /projects/{id}/approve
```

---

## 📌 TODO

* [ ] Подключить PostgreSQL
* [ ] Добавить JWT авторизацию
* [ ] Сделать frontend на React
* [ ] Role-based UI
* [ ] Улучшить AI-парсер
* [ ] Логирование действий

---

## 🧾 Лицензия

Private project / Internal use only

---

## 💡 Автор

AI-ERP System — система для автоматизации корпоративных закупок и документооборота.


