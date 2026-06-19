
```md
# 📊 CRM System (ERP Module)

![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-green?logo=fastapi)
![Docker](https://img.shields.io/badge/Docker-Container-blue?logo=docker)
![Status](https://img.shields.io/badge/Status-In%20Development-yellow)
![License](https://img.shields.io/badge/License-Private-lightgrey)

---

## 📌 Описание проекта

**CRM System** — корпоративная система управления проектами и закупками.

Система предназначена для автоматизации бизнес-процессов внутри компании:
- управление проектами
- обработка документов (PDF / Excel)
- контроль закупок и поставок
- распределение задач по ролям
- согласование этапов между отделами

---

## 🚀 Основные возможности

- 📦 Создание и ведение проектов закупок  
- 📄 Загрузка и обработка документов (PDF / Excel)  
- 👥 Ролевая модель доступа (RBAC)  
- 🔄 Workflow согласований (PM → Комдир → Бухгалтер → Склад)  
- 💰 Контроль счетов и оплат  
- 📊 Отслеживание статусов проектов  
- ⚙️ REST API для интеграций  

---

## 🧠 Технологии

- Python 3.12  
- FastAPI  
- Uvicorn  
- Docker  
- PostgreSQL (планируется)  

---

## 🏗️ Архитектура системы

```

Frontend (React)
↓
FastAPI Backend
↓
Business Logic Layer
↓
PostgreSQL Database

````

---

## ⚙️ Установка и запуск

### 📥 Клонирование

```bash
git clone <repo-url>
cd Ustem_group_crm
````

---

### 🐳 Docker запуск

```bash
docker build -t crm-system .
docker run -p 8000:8000 crm-system
```

---

### 💻 Локальный запуск

```bash
python -m venv venv
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows

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

## 👥 Роли в системе

### 👨‍💼 Project Manager (PM)

* Создание проектов
* Загрузка документов
* Проверка данных
* Редактирование товаров и цен

### 📊 Commercial Director

* Утверждение проектов
* Контроль бюджета и маржи

### 💰 Accountant

* Работа со счетами
* Финансовый контроль

### 📦 Warehouse Manager

* Отгрузка товаров
* Складской учет

---

## 🔄 Workflow

```
Создание проекта → Загрузка файла → Проверка PM → Утверждение →
Финансы → Отгрузка → Завершение
```

---

## 📡 API Endpoints

```http
POST /projects/create
POST /upload/file
GET  /projects/{id}
POST /projects/{id}/approve
```

---

## 📌 TODO

* [ ] Подключение PostgreSQL
* [ ] JWT авторизация
* [ ] Frontend на React
* [ ] Role-based UI
* [ ] Логирование действий
* [ ] Улучшение workflow

---

## 🧾 Лицензия

Private / Internal Use

---

## 💡 Проект

CRM система для автоматизации внутренних бизнес-процессов компании (закупки, проекты, документы, финансы).

```

---

Если хочешь, я могу дальше:
- делать README **как у реально стартапа (очень красивый UI стиль)**
- или помочь тебе правильно назвать проект (CRM / ERP / Procurement System)
- или подготовить тебе **презентацию для защиты проекта (очень важно для универа)**
```



