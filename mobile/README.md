# 📱 Universal Parser Mobile App

Кроссплатформенное мобильное приложение для мониторинга цен на товары с различных маркетплейсов.

## ✨ Возможности

### 🛍️ **Отслеживание товаров**
- **8 маркетплейсов**: Wildberries, Ozon, AliExpress, Amazon, eBay, Lamoda, DNS, Yandex
- **Автоматическое обновление** цен каждые 10 минут
- **История изменений** цен с графиками
- **Push уведомления** о изменениях цен
- **QR-код сканер** для быстрого добавления товаров

### 🤖 **AI функции**
- **Прогнозирование цен** на 1-30 дней
- **Анализ трендов** и сезонности
- **Обнаружение аномалий** в ценах
- **Персональные рекомендации** товаров
- **ML модели** для точных прогнозов

### 📊 **Аналитика**
- **Интерактивные графики** цен
- **Статистика по маркетплейсам**
- **Сравнение цен** между площадками
- **Экспорт данных** в Excel/PDF
- **Офлайн режим** с синхронизацией

## 🚀 Технологии

### **Frontend:**
- **Flutter 3.10+** - кроссплатформенная разработка
- **Riverpod** - управление состоянием
- **Go Router** - навигация
- **ScreenUtil** - адаптивный дизайн

### **UI/UX:**
- **Material Design 3** - современный дизайн
- **Custom animations** - плавные переходы
- **Dark/Light theme** - поддержка тем
- **Accessibility** - доступность

### **Backend Integration:**
- **REST API** - интеграция с FastAPI
- **Retrofit** - типизированные HTTP клиенты
- **Dio** - HTTP клиент с interceptors
- **WebSocket** - real-time обновления

### **Local Storage:**
- **Hive** - NoSQL база данных
- **SharedPreferences** - настройки
- **SQLite** - кэширование данных
- **Encryption** - шифрование данных

### **Features:**
- **Firebase** - push уведомления
- **QR Scanner** - сканирование кодов
- **Image Caching** - кэширование изображений
- **Offline Support** - работа без интернета

## 📱 Поддерживаемые платформы

- **iOS 12.0+** - iPhone и iPad
- **Android 6.0+** - все устройства
- **Web** - Progressive Web App
- **Desktop** - Windows, macOS, Linux

## 🛠️ Установка и запуск

### **Требования:**
- Flutter SDK 3.10+
- Dart 3.0+
- Android Studio / Xcode
- Git

### **Установка:**
```bash
# Клонирование репозитория
git clone https://github.com/your-repo/universal-parser.git
cd universal-parser/mobile

# Установка зависимостей
flutter pub get

# Генерация кода
flutter packages pub run build_runner build

# Запуск приложения
flutter run
```

### **Конфигурация:**
```dart
// lib/main.dart
void main() async {
  // Настройка API URL
  ApiServiceProvider.initialize(
    baseUrl: 'https://your-api.com/api/v1'
  );
  
  runApp(const UniversalParserApp());
}
```

## 📱 Скриншоты

### **Главный экран:**
- 📊 Обзор статистики системы
- 🛍️ Быстрые действия
- 📈 Последние товары
- 🔄 Обновление данных

### **Экран товаров:**
- 📋 Список всех товаров
- 🔍 Поиск и фильтрация
- 📊 Карточки товаров с ценами
- ⚙️ Управление товарами

### **AI Insights:**
- 🔮 Прогнозирование цен
- 📊 Анализ трендов
- 🚨 Обнаружение аномалий
- 💡 Рекомендации

### **Настройки:**
- ⚙️ Конфигурация приложения
- 🔔 Уведомления
- 🎨 Темы оформления
- 📱 О приложении

## 🏗️ Архитектура

### **Структура проекта:**
```
lib/
├── main.dart                 # Точка входа
├── models/                   # Модели данных
│   ├── item.dart
│   ├── marketplace.dart
│   └── ai.dart
├── services/                 # Сервисы
│   └── api_service.dart
├── providers/                # State management
│   ├── item_provider.dart
│   └── marketplace_provider.dart
├── screens/                  # Экраны
│   ├── home_screen.dart
│   ├── items_screen.dart
│   ├── ai_insights_screen.dart
│   └── settings_screen.dart
├── widgets/                  # UI компоненты
│   ├── item_card.dart
│   ├── stats_overview.dart
│   └── quick_actions.dart
└── utils/                    # Утилиты
    ├── constants.dart
    └── helpers.dart
```

### **State Management:**
- **Riverpod** - реактивное управление состоянием
- **AsyncValue** - обработка асинхронных данных
- **StateNotifier** - бизнес-логика
- **Provider** - внедрение зависимостей

### **Navigation:**
- **BottomNavigationBar** - основная навигация
- **MaterialPageRoute** - переходы между экранами
- **ModalBottomSheet** - модальные окна
- **Dialog** - диалоги

## 🔧 API Integration

### **Endpoints:**
```dart
// Items
GET    /api/v1/items/              # Список товаров
POST   /api/v1/items/              # Создание товара
PUT    /api/v1/items/{id}          # Обновление товара
DELETE /api/v1/items/{id}          # Удаление товара

// Marketplaces
GET    /api/v1/marketplaces/       # Список маркетплейсов
GET    /api/v1/marketplaces/{id}   # Детали маркетплейса

// AI
POST   /api/v1/ai/predict          # Прогнозирование цен
POST   /api/v1/ai/trends           # Анализ трендов
POST   /api/v1/ai/recommendations  # Рекомендации
```

### **Error Handling:**
```dart
try {
  final items = await ApiServiceProvider.instance.getItems();
  // Handle success
} catch (error) {
  // Handle error
  if (error is DioException) {
    switch (error.type) {
      case DioExceptionType.connectionTimeout:
        // Handle timeout
        break;
      case DioExceptionType.badResponse:
        // Handle HTTP error
        break;
      default:
        // Handle other errors
        break;
    }
  }
}
```

## 📊 Производительность

### **Оптимизации:**
- **Lazy loading** - ленивая загрузка списков
- **Image caching** - кэширование изображений
- **Data pagination** - пагинация данных
- **Background sync** - фоновое обновление

### **Метрики:**
- **Startup time** - < 3 секунд
- **Memory usage** - < 100MB
- **Battery usage** - оптимизировано
- **Network efficiency** - минимум запросов

## 🔔 Push Notifications

### **Firebase Integration:**
```dart
// Инициализация
await Firebase.initializeApp();

// Подписка на уведомления
await FirebaseMessaging.instance.requestPermission();

// Обработка уведомлений
FirebaseMessaging.onMessage.listen((RemoteMessage message) {
  // Handle notification
});
```

### **Типы уведомлений:**
- **Price alerts** - изменения цен
- **Stock alerts** - изменения наличия
- **AI insights** - новые прогнозы
- **System updates** - обновления системы

## 🎨 UI/UX Design

### **Design System:**
- **Primary Color**: #1f77b4 (Blue)
- **Secondary Colors**: Marketplace specific
- **Typography**: Roboto font family
- **Spacing**: 8dp grid system
- **Border Radius**: 8dp standard

### **Components:**
- **Cards** - товары, статистика
- **Buttons** - действия, навигация
- **Inputs** - поиск, формы
- **Charts** - графики цен
- **Modals** - диалоги, фильтры

### **Responsive Design:**
- **Mobile First** - приоритет мобильных устройств
- **Tablet Support** - поддержка планшетов
- **Landscape Mode** - альбомная ориентация
- **Accessibility** - доступность для всех

## 🧪 Тестирование

### **Unit Tests:**
```bash
flutter test test/unit/
```

### **Widget Tests:**
```bash
flutter test test/widget/
```

### **Integration Tests:**
```bash
flutter test integration_test/
```

### **Coverage:**
```bash
flutter test --coverage
genhtml coverage/lcov.info -o coverage/html
```

## 📦 Сборка и релиз

### **Debug Build:**
```bash
flutter build apk --debug
flutter build ios --debug
```

### **Release Build:**
```bash
flutter build apk --release
flutter build ios --release
```

### **App Bundle (Android):**
```bash
flutter build appbundle --release
```

### **IPA (iOS):**
```bash
flutter build ios --release
# Archive in Xcode
```

## 🚀 Развертывание

### **Google Play Store:**
1. Создать подписанный APK/AAB
2. Загрузить в Google Play Console
3. Настроить метаданные
4. Опубликовать

### **Apple App Store:**
1. Создать архив в Xcode
2. Загрузить в App Store Connect
3. Настроить метаданные
4. Отправить на ревью

### **Web Deployment:**
```bash
flutter build web --release
# Deploy to Firebase Hosting, Netlify, etc.
```

## 🔒 Безопасность

### **Data Protection:**
- **Encryption** - шифрование локальных данных
- **Secure Storage** - безопасное хранение
- **API Security** - HTTPS, токены
- **Privacy** - соблюдение GDPR

### **Authentication:**
- **JWT Tokens** - аутентификация
- **Biometric** - отпечатки, Face ID
- **Auto-logout** - автоматический выход
- **Session Management** - управление сессиями

## 📈 Аналитика

### **Firebase Analytics:**
- **User Engagement** - вовлеченность
- **Feature Usage** - использование функций
- **Crash Reports** - отчеты о сбоях
- **Performance** - производительность

### **Custom Events:**
```dart
// Отслеживание событий
Analytics.logEvent('item_added', parameters: {
  'marketplace': item.marketplace,
  'price': item.currentPrice,
});
```

## 🔄 Обновления

### **OTA Updates:**
- **CodePush** - обновления кода
- **Feature Flags** - флаги функций
- **A/B Testing** - A/B тестирование
- **Gradual Rollout** - постепенный релиз

### **Version Management:**
- **Semantic Versioning** - семантическое версионирование
- **Changelog** - журнал изменений
- **Migration** - миграция данных
- **Rollback** - откат версий

## 🤝 Вклад в проект

### **Development Setup:**
1. Fork репозитория
2. Создать feature branch
3. Внести изменения
4. Написать тесты
5. Создать Pull Request

### **Code Style:**
- **Dart/Flutter Lints** - линтеры
- **Prettier** - форматирование
- **Conventional Commits** - коммиты
- **Code Review** - ревью кода

## 📞 Поддержка

### **Документация:**
- **API Docs** - документация API
- **User Guide** - руководство пользователя
- **FAQ** - часто задаваемые вопросы
- **Troubleshooting** - решение проблем

### **Контакты:**
- **Email**: support@universal-parser.com
- **Telegram**: @universal_parser_support
- **GitHub Issues** - баг-репорты
- **Discord** - сообщество

---

**Universal Parser Mobile** - ваш умный помощник в мире e-commerce! 🚀📱


