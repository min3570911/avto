/**
 * Скрипт для управления цветом ковриков и окантовки, а также выбором комплектации
 */

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    // Инициализируем начальный выбор комплектации
    const selectedKitRadio = document.querySelector('input[name="selected_kit"]:checked');
    if (selectedKitRadio) {
        updateConfig(selectedKitRadio.value); // Handles price, active class for kit, etc.
        updateKitImage(selectedKitRadio.value); // Updates kit image
    } else {
        console.warn("No kit initially selected.");
        // Можно установить значение по умолчанию, если это необходимо, например:
        // const defaultKitCode = 'salon'; // Пример
        // const defaultKitRadio = document.querySelector(`input[name="selected_kit"][value="${defaultKitCode}"]`);
        // if (defaultKitRadio) {
        //    defaultKitRadio.checked = true;
        //    updateConfig(defaultKitCode);
        //    updateKitImage(defaultKitCode);
        // }
    }

    // Обновляем data-color-id по UUID из скрытого JSON и устанавливаем начальные значения для скрытых полей
    const colorMapScript = document.getElementById('color-map-json');
    let colorMap = {};
    if (colorMapScript && colorMapScript.textContent.trim() !== "") {
        try {
            colorMap = JSON.parse(colorMapScript.textContent);
        } catch (e) {
            console.error("Error parsing color-map-json:", e, ". Color selections might not work correctly.");
            // Критическая ошибка: без карты цветов UUID не будут установлены.
            // Можно рассмотреть вариант блокировки кнопки "В корзину" или уведомления пользователя.
        }
    } else {
        console.warn("color-map-json script tag not found or is empty. Color UUIDs will not be updated from map.");
    }

    // Обработка цветов коврика
    document.querySelectorAll('.color-picker[data-color-type="carpet"] .color-item').forEach(el => {
        const displayOrder = el.dataset.attrValue; // Используется как ключ в colorMap
        const initialColorIdPlaceholder = el.dataset.colorId; // e.g., "color-1", "color-6"

        if (colorMap[displayOrder]) {
            el.dataset.colorId = colorMap[displayOrder]; // Обновляем на реальный UUID
            if (el.classList.contains('active')) { // Если это цвет по умолчанию
                document.getElementById('carpet_color_input').value = colorMap[displayOrder];
            }
        } else {
            console.warn(`UUID not found in colorMap for carpet color with displayOrder: ${displayOrder} (initial placeholder: ${initialColorIdPlaceholder}). This color choice may be invalid.`);
            if (el.classList.contains('active')) {
                document.getElementById('carpet_color_input').value = ""; // Очищаем, чтобы не отправлять "color-X"
            }
            // Можно также деактивировать элемент 'el' или его data-color-id, чтобы он не отправлялся
            // el.dataset.colorId = ""; // Очищаем data-атрибут, чтобы activateColor тоже это увидел
        }
    });

    // Обработка цветов окантовки
    document.querySelectorAll('.color-picker[data-color-type="border"] .color-item').forEach(el => {
        const displayOrder = el.dataset.attrValue;
        const initialColorIdPlaceholder = el.dataset.colorId;

        if (colorMap[displayOrder]) {
            el.dataset.colorId = colorMap[displayOrder]; // Обновляем на реальный UUID
            if (el.classList.contains('active')) {
                document.getElementById('border_color_input').value = colorMap[displayOrder];
            }
        } else {
            console.warn(`UUID not found in colorMap for border color with displayOrder: ${displayOrder} (initial placeholder: ${initialColorIdPlaceholder}). This color choice may be invalid.`);
            if (el.classList.contains('active')) {
                document.getElementById('border_color_input').value = "";
            }
            // el.dataset.colorId = "";
        }
    });

    // Инициализируем обработчики событий
    setupEventHandlers();

    // Обновляем все скрытые поля форм (wishlist, cart) на основе текущих (уже обновленных) значений
    updateHiddenFields();

    // Первичный расчет цены на основе выбранных по умолчанию опций
    updatePrice();
});

/**
 * Устанавливает обработчики событий для интерактивных элементов
 */
function setupEventHandlers() {
    // Обработчики для выбора комплектации
    const kitRadios = document.querySelectorAll('input[name="selected_kit"]');
    kitRadios.forEach(radio => {
        radio.addEventListener('change', function() {
            updateConfig(this.value);
            updateKitImage(this.value);
            // updatePrice(); // updateConfig вызывает updatePrice
            // updateHiddenFields(); // updateConfig вызывает updateHiddenFields косвенно через updatePrice или напрямую
        });
    });

    // Обработчик для подпятника
    const podpCheck = document.getElementById('podp_check');
    if (podpCheck) {
        podpCheck.addEventListener('change', function() {
            updatePodp(); // Обновляет только иконку
            updatePrice(); // Пересчитывает цену
            updateHiddenFields(); // Обновляет скрытые поля форм
        });
    }

    // Обработчики для выбора цвета
    document.querySelectorAll('.color-item').forEach(item => {
        const colorPicker = item.closest('.color-picker');
        if (colorPicker && colorPicker.dataset.colorType) {
            const type = colorPicker.dataset.colorType;
            item.addEventListener('click', function() {
                activateColor(this, type); // Эта функция вызовет updateHiddenFields
                // updatePrice(); // Цена не зависит от цвета коврика/окантовки в текущей логике
            });
        }
    });

    // Обработчики для кнопок количества
    const plusBtn = document.getElementById('button-plus');
    const minusBtn = document.getElementById('button-minus');
    const quantityInput = document.getElementById('quantity');

    if (plusBtn && quantityInput) {
        plusBtn.addEventListener('click', function() {
            let quantity = parseInt(quantityInput.value) || 0;
            quantityInput.value = quantity + 1;
            updatePrice();
            updateHiddenFields();
        });
    }

    if (minusBtn && quantityInput) {
        minusBtn.addEventListener('click', function() {
            let quantity = parseInt(quantityInput.value) || 1;
            if (quantity > 1) {
                quantityInput.value = quantity - 1;
                updatePrice();
                updateHiddenFields();
            }
        });
    }

    if (quantityInput) {
        quantityInput.addEventListener('change', function() {
            let quantity = parseInt(this.value);
            if (isNaN(quantity) || quantity < 1) {
                this.value = '1'; // Сброс на 1 при невалидном значении
            }
            updatePrice();
            updateHiddenFields();
        });
    }

    const mainImage = document.getElementById('mainImage');
    if (mainImage) {
        mainImage.addEventListener('click', function() {
            this.classList.toggle('zoomed-in');
        });
    }
}

/**
 * Обновляет конфигурацию при выборе комплектации (стили активной опции)
 * @param {string} kitCode - Код выбранной комплектации
 */
function updateConfig(kitCode) {
    document.querySelectorAll('.kit-option-label').forEach(label => {
        const radio = label.querySelector('input[type="radio"]');
        if (radio && radio.value === kitCode) {
            label.classList.add('active');
        } else {
            label.classList.remove('active');
        }
    });
    updatePrice(); // Цена зависит от комплектации
    updateHiddenFields(); // Скрытые поля тоже
}

/**
 * Обновляет отображение подпятника (иконку)
 */
function updatePodp() {
    const podpElement = document.querySelector('.podpicon');
    const podpCheck = document.getElementById('podp_check');
    if (podpElement && podpCheck) {
        podpElement.style.display = podpCheck.checked ? 'block' : 'none';
    }
}

/**
 * Активирует выбранный цвет, обновляет изображение предпросмотра и скрытые поля.
 * @param {HTMLElement} element - Элемент цвета, который был нажат
 * @param {string} type - Тип цвета ('carpet' или 'border')
 */
function activateColor(element, type) {
    document.querySelectorAll(`.color-picker[data-color-type="${type}"] .color-item`).forEach(item => {
        item.classList.remove('active');
        item.style.border = '2px solid #ccc';
    });

    element.classList.add('active');
    element.style.border = '2px solid #FFEB3B';

    const colorId = element.dataset.colorId; // Должен быть UUID или пустая строка

    // Базовая проверка на UUID-подобную строку (наличие дефисов и длина)
    // Более строгая проверка может использовать regex: /^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$/
    const isPotentiallyValidUUID = colorId && colorId.includes('-') && colorId.length > 20;

    if (isPotentiallyValidUUID) {
        if (type === 'carpet') {
            document.getElementById('carpet_color_input').value = colorId;
        } else if (type === 'border') {
            document.getElementById('border_color_input').value = colorId;
        }
    } else {
        console.warn(`Attempted to activate color with invalid data-color-id: '${colorId}' for type: ${type}. Clearing corresponding hidden input.`);
        if (type === 'carpet') {
            document.getElementById('carpet_color_input').value = "";
        } else if (type === 'border') {
            document.getElementById('border_color_input').value = "";
        }
    }

    const attrId = parseInt(element.dataset.attrId); // Для обновления картинки предпросмотра
    const attrValue = element.dataset.attrValue;   // Порядковый номер для картинки

    if (attrId === 1) { // Цвет коврика
        const carpetImage = document.querySelector('.matcolor');
        if (carpetImage) carpetImage.src = `/media/images/schema/sota${attrValue}.png`;
    } else if (attrId === 2) { // Цвет окантовки
        const borderImage = document.querySelector('.bordercolor');
        if (borderImage) {
            const borderImageMap = {
                "1": "border211.png", "2": "border212.png", "3": "border213.png", "4": "border214.png",
                "5": "border215.png", "6": "border216.png", "7": "border217.png", "8": "border218.png",
                "9": "border219.png", "10": "border220.png", "11": "border221.png", "12": "border222.png",
                "13": "border223.png"
            };
            borderImage.src = `/media/images/schema/${borderImageMap[attrValue] || "border211.png"}`;
        }
    }
    updateHiddenFields();
}

/**
 * Обновляет цену на основе выбранной комплектации, подпятника и количества
 */
function updatePrice() {
    const selectedKitRadio = document.querySelector('input[name="selected_kit"]:checked');
    if (!selectedKitRadio) {
        // console.warn("updatePrice: No kit selected."); // Может быть вызвано при инициализации до выбора
        return;
    }
    const kitCode = selectedKitRadio.value;

    const kitDataContainer = document.getElementById('kit-variant-data');
    if (!kitDataContainer) {
        console.error("updatePrice: kit-variant-data element not found.");
        return;
    }

    const kitDataElement = kitDataContainer.querySelector(`div[data-kit-code="${kitCode}"]`);
    let kitPriceModifier = 0;
    if (kitDataElement && kitDataElement.dataset.kitPrice) {
        kitPriceModifier = parseFloat(kitDataElement.dataset.kitPrice);
        if (isNaN(kitPriceModifier)) {
            console.warn(`updatePrice: Kit price modifier for "${kitCode}" is NaN. Using 0.`);
            kitPriceModifier = 0;
        }
    } else {
        console.warn(`updatePrice: Data or price for kit code "${kitCode}" not found. Using 0 for modifier.`);
    }

    const basePriceMeta = document.querySelector('meta[name="product-price"]');
    if (!basePriceMeta) {
        console.error("updatePrice: meta tag with product-price not found.");
        return;
    }
    let basePrice = parseFloat(basePriceMeta.content);
    if (isNaN(basePrice)) {
        console.error("updatePrice: Base product price is NaN. Using 0.");
        basePrice = 0;
    }

    let podpPrice = 0;
    const podpCheck = document.getElementById('podp_check');
    if (podpCheck && podpCheck.checked) {
        const podpDataElement = kitDataContainer.querySelector('div[data-option-code="podpyatnik"]');
        if (podpDataElement && podpDataElement.dataset.optionPrice) {
            let optionPrice = parseFloat(podpDataElement.dataset.optionPrice);
            if (!isNaN(optionPrice)) {
                 podpPrice = optionPrice;
            } else {
                console.warn("updatePrice: Podpyatnik option price is NaN. Using 0.");
            }
        } else {
            console.warn("updatePrice: Podpyatnik option data or price not found. Using 0 for podpyatnik.");
        }
    }

    const quantityInput = document.getElementById('quantity');
    let quantity = 1;
    if (quantityInput) {
        quantity = parseInt(quantityInput.value);
        if (isNaN(quantity) || quantity < 1) {
            quantity = 1;
            quantityInput.value = '1';
        }
    }

    const totalPrice = (basePrice + kitPriceModifier + podpPrice) * quantity;
    const priceElement = document.getElementById('finalPrice');
    if (priceElement) {
        priceElement.textContent = `₹${totalPrice.toFixed(2)}`;
    }
}

/**
 * Обновляет все скрытые поля форм (для корзины и избранного)
 */
function updateHiddenFields() {
    const selectedKitRadio = document.querySelector('input[name="selected_kit"]:checked');
    // Пытаемся получить kitCode из выбранного radio, иначе из скрытого поля cart-kit (если оно уже было установлено), иначе 'salon'
    const cartKitInput = document.getElementById('cart-kit');
    const kitCode = selectedKitRadio ? selectedKitRadio.value : (cartKitInput ? cartKitInput.value : 'salon');

    const carpetColor = document.getElementById('carpet_color_input').value; // Должен быть UUID или ""
    const borderColor = document.getElementById('border_color_input').value; // Должен быть UUID или ""

    const podpCheck = document.getElementById('podp_check');
    const hasPodp = podpCheck && podpCheck.checked ? '1' : '0';

    const quantityInput = document.getElementById('quantity');
    const quantity = quantityInput ? (quantityInput.value || '1') : '1';

    // Wishlist form fields
    const wishlistFields = {
        'wishlist-kit': kitCode,
        'wishlist-carpet-color': carpetColor,
        'wishlist-border-color': borderColor,
        'wishlist-podp': hasPodp,
        'wishlist-quantity': quantity
    };
    for (const id in wishlistFields) {
        const el = document.getElementById(id);
        if (el) el.value = wishlistFields[id];
    }

    // Cart form fields
    const cartFields = {
        'cart-kit': kitCode,
        'cart-carpet-color': carpetColor,
        'cart-border-color': borderColor,
        'cart-podp': hasPodp,
        'cart-quantity': quantity
    };
    for (const id in cartFields) {
        const el = document.getElementById(id);
        if (el) el.value = cartFields[id];
    }
}

/**
 * Обновляет главное изображение продукта при клике на миниатюру
 * @param {string} src - Путь к изображению
 */
function updateMainImage(src) {
    const mainImage = document.getElementById('mainImage');
    if (mainImage) {
        mainImage.src = src;
        mainImage.classList.remove('zoomed-in');
    }
}

/**
 * Устанавливает URL для формы удаления отзыва
 * @param {string} actionUrl - URL действия формы
 */
function setDeleteAction(actionUrl) {
    const deleteForm = document.getElementById('deleteReviewForm');
    if (deleteForm) {
        deleteForm.action = actionUrl;
    }
}

/**
 * Отправляет лайк/дизлайк для отзыва (общая функция)
 * @param {string} reviewId - ID отзыва
 * @param {string} actionType - 'like' or 'dislike'
 */
function toggleReviewReaction(reviewId, actionType) {
    const csrfTokenInput = document.querySelector('input[name="csrfmiddlewaretoken"]');
    if (!csrfTokenInput) {
        console.error("CSRF token input not found.");
        return;
    }
    const csrfToken = csrfTokenInput.value;

    // Убедитесь, что URL формируется правильно. Пример: /product/like-review/UUID/
    fetch(`/product/${actionType}-review/${reviewId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken,
            'Content-Type': 'application/json'
        },
    })
    .then(response => {
        if (!response.ok) {
            // Попытка получить текст ошибки от сервера, если есть
            return response.text().then(text => {
                throw new Error(`Network response was not ok: ${response.status} ${response.statusText}. Server said: ${text}`);
            });
        }
        return response.json();
    })
    .then(data => {
        const likeCountEl = document.getElementById(`like-count-${reviewId}`);
        const dislikeCountEl = document.getElementById(`dislike-count-${reviewId}`);
        if (likeCountEl) likeCountEl.innerText = data.likes !== undefined ? data.likes : 'N/A';
        if (dislikeCountEl) dislikeCountEl.innerText = data.dislikes !== undefined ? data.dislikes : 'N/A';
    })
    .catch(error => {
        console.error(`Error during ${actionType} review for ${reviewId}:`, error);
    });
}

function toggleLike(reviewId) {
    toggleReviewReaction(reviewId, 'like');
}

function toggleDislike(reviewId) {
    toggleReviewReaction(reviewId, 'dislike');
}

/**
 * Обновляет изображение комплектации в соответствии с выбранным кодом комплектации
 * @param {string} kitCode - Код выбранной комплектации
 */
function updateKitImage(kitCode) {
    const kitDataContainer = document.getElementById('kit-variant-data');
    const kitImageElement = document.getElementById('kit-image');

    if (!kitImageElement) {
        console.error("updateKitImage: kit-image img element not found.");
        return;
    }
    // Путь по умолчанию, если информация не найдена или изображение не указано
    let imagePath = '/media/images/schema/salon.png';

    if (kitDataContainer) {
        const kitInfoDiv = kitDataContainer.querySelector(`div[data-kit-code="${kitCode}"]`);
        if (kitInfoDiv) {
            if (kitInfoDiv.dataset.kitImage && kitInfoDiv.dataset.kitImage.trim() !== "") {
                imagePath = kitInfoDiv.dataset.kitImage;
            } else {
                // console.warn(`updateKitImage: Image path not found or empty for kit code "${kitCode}". Using default.`);
            }
        } else {
            // console.warn(`updateKitImage: Data for kit code "${kitCode}" not found. Using default image.`);
        }
    } else {
        console.warn("updateKitImage: kit-variant-data element not found. Using default image for kit.");
    }

    kitImageElement.src = imagePath;
}