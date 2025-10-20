"""API эндпоинты для интернационализации и локализации"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.core.i18n import i18n_manager, get_text, format_currency, format_datetime, is_rtl
from app.services.currency_service import currency_service
from app.services.timezone_service import timezone_service

router = APIRouter()


class TranslationRequest(BaseModel):
    """Запрос на перевод"""
    key: str
    locale: str
    parameters: Optional[Dict[str, Any]] = None


class CurrencyConversionRequest(BaseModel):
    """Запрос на конвертацию валюты"""
    amount: float
    from_currency: str
    to_currency: str


class TimezoneConversionRequest(BaseModel):
    """Запрос на конвертацию часового пояса"""
    datetime: datetime
    from_timezone: str
    to_timezone: str


@router.get("/locales")
async def get_supported_locales():
    """Получить список поддерживаемых локалей"""
    locales = i18n_manager.get_supported_locales()
    return {
        "locales": locales,
        "total": len(locales),
        "default": i18n_manager.default_locale
    }


@router.get("/locales/{locale_code}")
async def get_locale_info(locale_code: str):
    """Получить информацию о локали"""
    locale_info = i18n_manager.get_locale_info(locale_code)
    if not locale_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Locale not found"
        )
    return locale_info


@router.get("/translations")
async def get_translations(
    locale: str = Query(..., description="Код локали"),
    namespace: Optional[str] = Query(None, description="Пространство имен (например, common, navigation)")
):
    """Получить переводы для локали"""
    if locale not in i18n_manager.supported_locales:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported locale"
        )
    
    translations = i18n_manager.translations.get(locale, {})
    
    if namespace:
        translations = translations.get(namespace, {})
    
    return {
        "locale": locale,
        "namespace": namespace,
        "translations": translations
    }


@router.post("/translations")
async def add_translation(
    request: TranslationRequest,
    db: Session = Depends(get_db)
):
    """Добавить перевод"""
    if request.locale not in i18n_manager.supported_locales:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported locale"
        )
    
    # В реальном приложении здесь была бы валидация и сохранение в БД
    i18n_manager.add_translation(
        request.key,
        request.parameters.get("value", ""),
        request.locale
    )
    
    return {
        "message": "Translation added successfully",
        "key": request.key,
        "locale": request.locale
    }


@router.get("/text/{key}")
async def get_translated_text(
    key: str,
    locale: str = Query(..., description="Код локали"),
    **kwargs
):
    """Получить переведенный текст"""
    if locale not in i18n_manager.supported_locales:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported locale"
        )
    
    text = get_text(key, locale, **kwargs)
    
    return {
        "key": key,
        "locale": locale,
        "text": text,
        "is_rtl": is_rtl(locale)
    }


@router.get("/currencies")
async def get_supported_currencies():
    """Получить список поддерживаемых валют"""
    currencies = currency_service.get_supported_currencies()
    return {
        "currencies": [
            {
                "code": currency.code,
                "name": currency.name,
                "symbol": currency.symbol,
                "decimal_places": currency.decimal_places,
                "is_crypto": currency.is_crypto
            }
            for currency in currencies
        ],
        "total": len(currencies)
    }


@router.get("/currencies/{currency_code}")
async def get_currency_info(currency_code: str):
    """Получить информацию о валюте"""
    currency_info = currency_service.get_currency_info(currency_code)
    if not currency_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Currency not found"
        )
    
    return {
        "code": currency_info.code,
        "name": currency_info.name,
        "symbol": currency_info.symbol,
        "decimal_places": currency_info.decimal_places,
        "is_crypto": currency_info.is_crypto,
        "emoji": currency_service.get_currency_emoji(currency_code)
    }


@router.post("/currencies/convert")
async def convert_currency(request: CurrencyConversionRequest):
    """Конвертировать валюту"""
    if not currency_service.is_currency_supported(request.from_currency):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported currency: {request.from_currency}"
        )
    
    if not currency_service.is_currency_supported(request.to_currency):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported currency: {request.to_currency}"
        )
    
    from decimal import Decimal
    amount = Decimal(str(request.amount))
    
    converted_amount = await currency_service.convert_currency(
        amount,
        request.from_currency,
        request.to_currency
    )
    
    if converted_amount is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Currency conversion failed"
        )
    
    return {
        "from_currency": request.from_currency,
        "to_currency": request.to_currency,
        "amount": float(amount),
        "converted_amount": float(converted_amount),
        "rate": float(converted_amount / amount) if amount != 0 else 0
    }


@router.get("/currencies/rates")
async def get_exchange_rates(
    from_currency: str = Query(..., description="Базовая валюта"),
    to_currencies: str = Query(..., description="Целевые валюты через запятую")
):
    """Получить курсы валют"""
    if not currency_service.is_currency_supported(from_currency):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported currency: {from_currency}"
        )
    
    to_currency_list = [curr.strip() for curr in to_currencies.split(",")]
    
    rates = await currency_service.get_multiple_rates(from_currency, to_currency_list)
    
    return {
        "base_currency": from_currency,
        "rates": rates,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/timezones")
async def get_supported_timezones():
    """Получить список поддерживаемых часовых поясов"""
    timezones = timezone_service.get_popular_timezones()
    return {
        "timezones": [
            {
                "name": tz.name,
                "display_name": tz.display_name,
                "utc_offset": tz.utc_offset,
                "country": tz.country,
                "city": tz.city,
                "is_dst": tz.is_dst,
                "emoji": timezone_service.get_timezone_emoji(tz.name)
            }
            for tz in timezones
        ],
        "total": len(timezones)
    }


@router.get("/timezones/{timezone_name}")
async def get_timezone_info(timezone_name: str):
    """Получить информацию о часовом поясе"""
    timezone_info = timezone_service.get_timezone_info(timezone_name)
    if not timezone_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Timezone not found"
        )
    
    return {
        "name": timezone_info.name,
        "display_name": timezone_info.display_name,
        "utc_offset": timezone_info.utc_offset,
        "country": timezone_info.country,
        "city": timezone_info.city,
        "is_dst": timezone_info.is_dst,
        "emoji": timezone_service.get_timezone_emoji(timezone_name),
        "abbreviation": timezone_service.get_timezone_abbreviation(timezone_name)
    }


@router.post("/timezones/convert")
async def convert_timezone(request: TimezoneConversionRequest):
    """Конвертировать дату и время между часовыми поясами"""
    try:
        converted_datetime = timezone_service.convert_datetime(
            request.datetime,
            request.from_timezone,
            request.to_timezone
        )
        
        return {
            "original_datetime": request.datetime.isoformat(),
            "from_timezone": request.from_timezone,
            "to_timezone": request.to_timezone,
            "converted_datetime": converted_datetime.isoformat(),
            "utc_offset_from": timezone_service.get_utc_offset(request.from_timezone),
            "utc_offset_to": timezone_service.get_utc_offset(request.to_timezone),
            "time_difference": timezone_service.get_timezone_difference(
                request.from_timezone,
                request.to_timezone
            )
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Timezone conversion failed: {str(e)}"
        )


@router.get("/timezones/current/{timezone_name}")
async def get_current_time(timezone_name: str):
    """Получить текущее время в часовом поясе"""
    try:
        current_time = timezone_service.get_current_time(timezone_name)
        
        return {
            "timezone": timezone_name,
            "current_time": current_time.isoformat(),
            "utc_offset": timezone_service.get_utc_offset(timezone_name),
            "abbreviation": timezone_service.get_timezone_abbreviation(timezone_name),
            "is_dst": timezone_service.is_dst_active(timezone_name)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get current time: {str(e)}"
        )


@router.get("/timezones/groups")
async def get_timezone_groups():
    """Получить часовые пояса, сгруппированные по регионам"""
    groups = timezone_service.get_timezone_groups()
    
    return {
        "groups": {
            region: [
                {
                    "name": tz.name,
                    "display_name": tz.display_name,
                    "utc_offset": tz.utc_offset,
                    "country": tz.country,
                    "city": tz.city,
                    "is_dst": tz.is_dst,
                    "emoji": timezone_service.get_timezone_emoji(tz.name)
                }
                for tz in timezones
            ]
            for region, timezones in groups.items()
        }
    }


@router.get("/timezones/working-hours/{timezone_name}")
async def get_working_hours(
    timezone_name: str,
    start_hour: int = Query(9, ge=0, le=23, description="Час начала рабочего дня"),
    end_hour: int = Query(17, ge=0, le=23, description="Час окончания рабочего дня")
):
    """Получить рабочие часы для часового пояса"""
    try:
        working_hours = timezone_service.get_working_hours(timezone_name, start_hour, end_hour)
        
        return {
            "timezone": timezone_name,
            "current_time": working_hours["current_time"].isoformat(),
            "work_start": working_hours["work_start"].isoformat() if working_hours["work_start"] else None,
            "work_end": working_hours["work_end"].isoformat() if working_hours["work_end"] else None,
            "is_workday": working_hours["is_workday"],
            "is_working_hours": working_hours["is_working_hours"],
            "next_work_start": working_hours["next_work_start"].isoformat() if working_hours["next_work_start"] else None,
            "time_until_work_start": str(working_hours["time_until_work_start"]),
            "time_until_work_end": str(working_hours["time_until_work_end"])
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get working hours: {str(e)}"
        )


@router.get("/detect-language")
async def detect_language(
    text: str = Query(..., description="Текст для определения языка")
):
    """Определить язык текста"""
    if not text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Text cannot be empty"
        )
    
    detected_language = i18n_manager.detect_language(text)
    locale_info = i18n_manager.get_locale_info(detected_language)
    
    return {
        "text": text,
        "detected_language": detected_language,
        "confidence": 0.85,  # Заглушка для уверенности
        "locale_info": locale_info,
        "is_rtl": is_rtl(detected_language)
    }


@router.get("/format/currency")
async def format_currency_amount(
    amount: float = Query(..., description="Сумма"),
    currency: str = Query(..., description="Код валюты"),
    locale: str = Query("en", description="Код локали")
):
    """Форматировать валюту"""
    if not currency_service.is_currency_supported(currency):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported currency: {currency}"
        )
    
    if locale not in i18n_manager.supported_locales:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported locale"
        )
    
    formatted_amount = currency_service.format_currency(
        currency_service.convert_currency(amount, currency, currency) or amount,
        currency,
        locale
    )
    
    return {
        "amount": amount,
        "currency": currency,
        "locale": locale,
        "formatted": formatted_amount,
        "symbol": currency_service.get_currency_symbol(currency),
        "name": currency_service.get_currency_name(currency, locale)
    }


@router.get("/format/datetime")
async def format_datetime_string(
    datetime_str: str = Query(..., description="Дата и время в ISO формате"),
    locale: str = Query("en", description="Код локали"),
    timezone: Optional[str] = Query(None, description="Часовой пояс")
):
    """Форматировать дату и время"""
    try:
        dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid datetime format"
        )
    
    if locale not in i18n_manager.supported_locales:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported locale"
        )
    
    formatted_datetime = format_datetime(dt, locale, timezone)
    
    return {
        "datetime": datetime_str,
        "locale": locale,
        "timezone": timezone,
        "formatted": formatted_datetime,
        "is_rtl": is_rtl(locale)
    }


@router.get("/rtl-languages")
async def get_rtl_languages():
    """Получить список RTL языков"""
    rtl_languages = [
        {
            "code": lang,
            "name": i18n_manager.get_locale_info(lang)["name"],
            "is_rtl": True
        }
        for lang in i18n_manager.rtl_languages
    ]
    
    return {
        "rtl_languages": rtl_languages,
        "total": len(rtl_languages)
    }


@router.get("/country-settings/{country_code}")
async def get_country_settings(country_code: str):
    """Получить настройки для страны"""
    timezone = timezone_service.get_timezone_by_country(country_code)
    currency = currency_service.get_currency_by_country(country_code)
    
    return {
        "country_code": country_code,
        "timezone": timezone,
        "currency": currency,
        "locale": f"en-{country_code.lower()}",  # Заглушка
        "is_rtl": False  # Заглушка
    }


@router.get("/locale-settings/{locale}")
async def get_locale_settings(locale: str):
    """Получить настройки для локали"""
    if locale not in i18n_manager.supported_locales:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Locale not found"
        )
    
    timezone = timezone_service.get_timezone_by_locale(locale)
    currency = currency_service.get_currency_by_locale(locale)
    locale_info = i18n_manager.get_locale_info(locale)
    
    return {
        "locale": locale,
        "timezone": timezone,
        "currency": currency,
        "is_rtl": locale_info["is_rtl"],
        "language": locale_info["language"],
        "territory": locale_info["territory"],
        "display_name": locale_info["name"]
    }


