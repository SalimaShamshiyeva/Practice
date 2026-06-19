# AI-ERP — Система управления закупками с AI-парсингом

Корпоративная ERP-система для управления проектами закупок с AI-ассистентом на базе GPT-4o-mini.

---

## Технологии

| Слой | Технология |
|------|------------|
| Frontend | React 18 + TypeScript + Ant Design 5 |
| Backend | Python 3.12 + Django 4.2 + DRF |
| База данных | PostgreSQL 16 + SQLAlchemy 2.0 |
| Валидация | Pydantic 2 |
| AI | OpenAI GPT-4o-mini |
| Кэш/Очереди | Redis + Celery |
| Деплой | Docker Compose + Nginx + Gunicorn |

---

## Быстрый старт

### 1. Требования

- Docker 24+ и Docker Compose 2+
- OpenAI API ключ

### 2. Клонирование и конфигурация

```bash
git clone <repo-url> ai-erp && cd ai-erp
cp .env.example .env
```

Отредактируйте `.env`:
```
OPENAI_API_KEY=sk-ваш-ключ
DJANGO_SECRET_KEY=сгенерируйте-случайный-ключ
DB_PASSWORD=надёжный-пароль
```

### 3. Запуск

```bash
docker compose up -d
```

При первом запуске автоматически:
- Применятся миграции
- Сидируются тестовые данные (пользователи, товары, поставщики)

### 4. Доступ

| Сервис | URL |
|--------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000/api/v1/ |
| Admin panel | http://localhost:8000/admin/ |

---

## Тестовые аккаунты

| Логин | Пароль | Роль |
|-------|--------|------|
| `pm_demo` | `demo1234!` | Проектный менеджер |
| `komdir_demo` | `demo1234!` | Коммерческий директор |
| `buh_demo` | `demo1234!` | Бухгалтер |
| `zav_demo` | `demo1234!` | Заведующий складом |

---

## Архитектура системы

```
Frontend (React + TypeScript + Ant Design)
├── LoginPage
├── DashboardPage (role-specific)
├── ProjectsPage → ProjectDetailPage
├── AIParserPage (PDF/Excel → смета)
├── InvoicesPage (Комдир + Бухгалтер)
├── WarehousePage (Завсклад)
└── AuditPage

Backend (Django + DRF)
├── JWT Authentication Layer
├── Role Permission Layer
│   ├── IsPM, IsKomdir, IsBuhgalter, IsZavsklad
│   └── CanTransitionStatus, CanEditProject
├── Business Logic Layer
│   ├── State Machine (14 статусов)
│   ├── Price Deviation Checker (20% threshold)
│   ├── Document Generator (python-docx)
│   └── Audit Logger (all mutations)
├── AI Service Layer
│   ├── DocumentExtractor (PDF via pdfplumber, Excel via pandas)
│   ├── AIParser (GPT-4o-mini, temperature=0)
│   └── PriceChecker (DB-only, no internet)
└── Warehouse Service

Database (PostgreSQL)
├── User (roles: pm/komdir/buhgalter/zavsklad/admin)
├── Project (state machine, doc checklist)
├── EstimateItem (price flagging)
├── Product + ProductCategory + PriceHistory
├── Supplier + SupplierPriceList
├── SupplierInvoice (AI → Komdir → Buhgalter routing)
├── WarehouseItem (reserve/ship guards)
└── AuditLog (immutable event log)
```

---

## Жизненный цикл проекта

```
Черновик
  ↓ (ПМ)
На проверке ПМ
  ↓ (ПМ)
На утверждении Комдира
  ↓ (Комдир)
КП утверждено
  ↓ (ПМ — генерация договора)
Ожидание подписания
  ↓ (ПМ — подписание)
Активный закуп
  ↓ (ПМ — выставление счетов)
Закупка [AI проверка → Комдир одобрение → Бухгалтер]
  ↓ (Бухгалтер — оплата)
Ожидание оплаты → Оплачено
  ↓ (Завсклад)
На складе → В резерве → Отгружено
  ↓ (Бухгалтер — закрывающие документы)
Документы проверяются
  ↓ (Бухгалтер — все 4 документа)
Завершено ✓
```

---

## Ролевая система

### ПМ (Проектный менеджер)
- Создаёт проекты
- Загружает документы для AI-парсинга
- Редактирует смету
- Отправляет на проверку/утверждение
- Генерирует и подписывает договоры
- Выставляет счета поставщиков (→ AI→Комдир, не напрямую)

### Комдир (Коммерческий директор)
- Утверждает/отклоняет проекты на этапе КП
- Видит ВСЕ проекты
- Одобряет счета поставщиков (приходят от AI)
- Одобряет позиции с отклонением цены >20%

### Бухгалтер
- Видит проекты со статусом: waiting_payment, paid, docs_check, completed
- Видит только ОДОБРЕННЫЕ Комдиром счета
- Производит оплату счетов
- Ведёт чек-лист документов (ДОВ, ЭСФ, накладная, АВР)
- Закрывает проект после полного чек-листа

### Завсклад
- Видит проекты: paid, in_warehouse, reserved, shipped
- Принимает товар на склад
- Резервирует под проекты
- Производит отгрузку
- Нельзя: отрицательный остаток, двойной резерв, повторная отгрузка

---

## AI-Парсер

### Поддерживаемые форматы
- PDF (pdfplumber)
- Excel .xlsx / .xls (pandas)

### Процесс обработки
1. Извлечение текста из документа
2. Отправка в GPT-4o-mini (temperature=0, JSON mode)
3. Извлечение: наименование + количество
4. Дедупликация по имени
5. Проверка цен **только в БД** (Products, PriceHistory, SupplierPriceList)
6. Маркировка: 🟢 На складе / 🟡 Историческая / 🔴 Новый товар
7. Возврат отредактируемой сметы

### Контроль цен
- Порог: 20% (настраивается `PRICE_DEVIATION_THRESHOLD`)
- При превышении: красный алерт + блокировка + требование комментария ПМ
- Маршрут: AI flag → ПМ комментарий → Комдир (не Бухгалтер!)

---

## API Endpoints

```
POST   /api/v1/auth/token/                    Получить JWT
POST   /api/v1/auth/refresh/                  Обновить токен
GET    /api/v1/auth/me/                        Текущий пользователь

GET    /api/v1/projects/                       Список проектов (role-filtered)
POST   /api/v1/projects/                       Создать проект (PM only)
GET    /api/v1/projects/{id}/                  Детали проекта
POST   /api/v1/projects/{id}/transition/       Сменить статус
POST   /api/v1/projects/{id}/generate_contract/ Сгенерировать договор
POST   /api/v1/projects/{id}/sign_contract/    Подписать договор
PATCH  /api/v1/projects/{id}/update_docs_checklist/ Обновить чек-лист
GET    /api/v1/projects/{id}/audit_trail/      История изменений

GET    /api/v1/projects/{id}/estimate-items/  Позиции сметы
POST   /api/v1/projects/{id}/estimate-items/  Добавить позицию
PATCH  /api/v1/projects/{id}/estimate-items/{id}/ Обновить позицию
DELETE /api/v1/projects/{id}/estimate-items/{id}/ Удалить позицию
POST   /api/v1/projects/{id}/estimate-items/{id}/approve_price/ Одобрить цену

GET    /api/v1/projects/{id}/invoices/        Счета проекта
POST   /api/v1/projects/{id}/invoices/        Выставить счёт (→ AI check)
POST   /api/v1/projects/{id}/invoices/{id}/approve/    Одобрить (Komdir)
POST   /api/v1/projects/{id}/invoices/{id}/mark_paid/  Оплатить (Buhgalter)

GET    /api/v1/invoices/                       Глобальный список (role-filtered)

GET    /api/v1/warehouse/                      Склад
POST   /api/v1/warehouse/{id}/reserve/         Зарезервировать
POST   /api/v1/warehouse/{id}/ship/            Отгрузить

POST   /api/v1/ai/parse/                       AI-парсинг документа

GET    /api/v1/audit/                          Журнал аудита
GET    /api/v1/dashboard/                      Дашборд (role-specific)
```

---

## Запуск тестов

```bash
# В контейнере backend
docker compose exec backend python manage.py test erp.tests

# Или локально
cd backend
python manage.py test erp.tests --verbosity=2
```

---

## Безопасность

- JWT auth (8ч access / 1д refresh)
- Role-based permission classes на каждом endpoint
- State machine блокирует переходы без авторизации
- Invoice routing: AI → только Комдир (Бухгалтер не получает pending_ai/pending_komdir)
- Warehouse: clean() validation на отрицательные остатки
- AuditLog: неизменяемая история всех мутаций
- CORS настроен явно
- SQL injection защита через ORM
- File upload validation: тип + размер (≤50MB)

---

## Структура файлов

```
ai-erp/
├── docker-compose.yml
├── .env.example
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── config/
│   │   ├── settings.py        Django settings
│   │   └── urls.py            URL routing
│   └── erp/
│       ├── models.py          All DB models + state machine
│       ├── views.py           All API views
│       ├── serializers.py     DRF serializers
│       ├── permissions.py     Role permission classes
│       ├── middleware.py      Audit middleware
│       ├── exceptions.py      Custom exception handler
│       ├── services/
│       │   ├── ai_service.py  AI parsing + price check
│       │   └── document_service.py  Contract generation
│       ├── management/commands/
│       │   └── seed_data.py   Test data seeding
│       └── tests/
│           └── test_erp.py    Unit + integration tests
└── frontend/
    ├── Dockerfile
    ├── nginx.conf
    ├── package.json
    └── src/
        ├── App.tsx            Main app + routing
        ├── types/index.ts     TypeScript types
        ├── services/api.ts    API client
        ├── store/auth.tsx     Auth state
        └── pages/
            ├── LoginPage.tsx
            ├── DashboardPage.tsx
            ├── ProjectsPage.tsx
            ├── ProjectCreatePage.tsx
            ├── ProjectDetailPage.tsx
            ├── AIParserPage.tsx
            ├── InvoicesPage.tsx
            ├── WarehousePage.tsx
            └── AuditPage.tsx
```
