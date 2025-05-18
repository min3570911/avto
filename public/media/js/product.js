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
  }

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

  // Обработчики для выбора цвета коврика
  document.querySelectorAll('.color-picker[data-color-type="carpet"] .color-item').forEach(item => {
    if (item.dataset.isAvailable !== 'false') {
      item.addEventListener('click', function() {
        activateColor(this, 'carpet');
      });
    }
  });

  // Обработчики для выбора цвета окантовки
  document.querySelectorAll('.color-picker[data-color-type="border"] .color-item').forEach(item => {
    if (item.dataset.isAvailable !== 'false') {
      item.addEventListener('click', function() {
        activateColor(this, 'border');
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

  // Проверка доступности цветов перед отправкой формы
  const addToCartForm = document.getElementById('cart-form');
  if (addToCartForm) {
    addToCartForm.addEventListener('submit', function(event) {
      const carpetColorId = document.getElementById('cart-carpet-color').value;
      const borderColorId = document.getElementById('cart-border-color').value;

      // Проверка, что выбранные цвета доступны
      let carpetColorAvailable = false;
      let borderColorAvailable = false;

      document.querySelectorAll('.color-picker[data-color-type="carpet"] .color-item').forEach(item => {
        if (item.dataset.colorUuid === carpetColorId && item.dataset.isAvailable === 'true') {
          carpetColorAvailable = true;
        }
      });

      document.querySelectorAll('.color-picker[data-color-type="border"] .color-item').forEach(item => {
        if (item.dataset.colorUuid === borderColorId && item.dataset.isAvailable === 'true') {
          borderColorAvailable = true;
        }
      });

      if (!carpetColorAvailable || !borderColorAvailable) {
        event.preventDefault();
        alert('Пожалуйста, выберите доступные цвета для коврика и окантовки');
      }
    });
  }

  // То же самое для формы избранного
  const wishlistForm = document.getElementById('wishlist-form');
  if (wishlistForm) {
    wishlistForm.addEventListener('submit', function(event) {
      const carpetColorId = document.getElementById('wishlist-carpet-color').value;
      const borderColorId = document.getElementById('wishlist-border-color').value;

      let carpetColorAvailable = false;
      let borderColorAvailable = false;

      document.querySelectorAll('.color-picker[data-color-type="carpet"] .color-item').forEach(item => {
        if (item.dataset.colorUuid === carpetColorId && item.dataset.isAvailable === 'true') {
          carpetColorAvailable = true;
        }
      });

      document.querySelectorAll('.color-picker[data-color-type="border"] .color-item').forEach(item => {
        if (item.dataset.colorUuid === borderColorId && item.dataset.isAvailable === 'true') {
          borderColorAvailable = true;
        }
      });

      if (!carpetColorAvailable || !borderColorAvailable) {
        event.preventDefault();
        alert('Пожалуйста, выберите доступные цвета для коврика и окантовки');
      }
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
  // Проверяем доступность цвета
  const isAvailable = element.dataset.isAvailable === 'true';
  if (!isAvailable) {
    console.warn('Попытка выбора недоступного цвета');
    return; // Игнорируем клик на недоступный цвет
  }

  // Убираем активный класс у всех элементов того же типа
  document.querySelectorAll(`.color-picker[data-color-type="${type}"] .color-item`).forEach(item => {
    item.classList.remove('active');
    item.style.border = '2px solid #ccc';
  });

  // Добавляем активный класс выбранному элементу
  element.classList.add('active');
  element.style.border = '2px solid #FFEB3B';

  // Получаем UUID цвета и URL изображения
  const colorUUID = element.getAttribute('data-color-uuid');
  const imageUrl = element.getAttribute('data-image-url');

  // Обновляем соответствующие скрытые поля
  if (type === 'carpet') {
    document.getElementById('carpet_color_input').value = colorUUID;

    // Обновляем поля для корзины и избранного
    const cartField = document.getElementById('cart-carpet-color');
    const wishlistField = document.getElementById('wishlist-carpet-color');

    if (cartField) cartField.value = colorUUID;
    if (wishlistField) wishlistField.value = colorUUID;

    // Обновляем изображение коврика
    const carpetImage = document.querySelector('.matcolor');
    if (carpetImage && imageUrl) {
      carpetImage.src = imageUrl;
    }
  } else if (type === 'border') {
    document.getElementById('border_color_input').value = colorUUID;

    // Обновляем поля для корзины и избранного
    const cartField = document.getElementById('cart-border-color');
    const wishlistField = document.getElementById('wishlist-border-color');

    if (cartField) cartField.value = colorUUID;
    if (wishlistField) wishlistField.value = colorUUID;

    // Обновляем изображение окантовки
    const borderImage = document.querySelector('.bordercolor');
    if (borderImage && imageUrl) {
      borderImage.src = imageUrl;
    }
  }

  // Сообщаем о смене цвета
  console.log(`Выбран ${type === 'carpet' ? 'цвет коврика' : 'цвет окантовки'}: ${element.title}`);
}

/**
 * Обновляет цену на основе выбранной комплектации, подпятника и количества
 */
function updatePrice() {
  const selectedKitRadio = document.querySelector('input[name="selected_kit"]:checked');
  if (!selectedKitRadio) {
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
      }
    }
  } else {
    console.warn("updateKitImage: kit-variant-data element not found. Using default image for kit.");
  }

  kitImageElement.src = imagePath;
}