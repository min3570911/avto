/**
 * product.js - Скрипт для страницы продукта с визуализацией ковриков
 *
 * Функциональность:
 * - Визуализация ковриков с разными цветами и окантовкой
 * - Визуализация разных комплектаций
 * - Обработка выбора подпятника
 * - Обработка лайков/дизлайков отзывов
 * - Эффект зума для изображений
 */

// Таблица соответствия атрибутов и их идентификаторов
const attributeIds = {
  "CARPET_COLOR": 1,   // Цвет коврика
  "BORDER_COLOR": 2,   // Цвет окантовки
  "PODPYATNIK": 7      // Наличие подпятника
};

// Таблица соответствия цвета и названия коврика
const carpetColors = {
  1: "Черный",
  2: "Красный",
  3: "Серый",
  4: "Темно-синий",
  5: "Коричневый",
  6: "Бежевый",
  7: "Синий",
  8: "Салатовый",
  9: "Фиолетовый",
  10: "Оранжевый"
};

// Таблица соответствия цвета окантовки и файла изображения
const borderColorToImage = {
  1: "border211.png",  // Черный
  2: "border212.png",  // Серый
  3: "border213.png",  // Коричневый
  4: "border214.png",  // Бежевый
  5: "border215.png",  // Синий
  6: "border216.png",  // Темно-синий
  7: "border217.png",  // Красный
  8: "border218.png",  // Бордовый
  9: "border219.png",  // Желтый
  10: "border220.png", // Зеленый
  11: "border221.png", // Темно-зеленый
  12: "border222.png", // Фиолетовый
  13: "border223.png"  // Оранжевый
};

// Таблица соответствия комплектаций и файлов схем (резервная)
const kitToSchemaImage = {
  'salon': 'salon.png',
  'trunk': 'trunk.png',
  'salon_trunk': 'salon_trunk.png',
  'driver_only': 'driver_only.png',
  'front_only': 'front_only.png'
};

/**
 * Предзагрузка изображений для более быстрого переключения.
 */
function preloadImages() {
  // Предзагрузка изображений ковриков
  for (let i = 1; i <= 10; i++) {
    const img = new Image();
    img.src = `/media/images/schema/sota${i}.png`;
  }

  // Предзагрузка изображений окантовки
  for (let i = 1; i <= 13; i++) {
    const key = i.toString();
    if (borderColorToImage[key]) {
      const img = new Image();
      img.src = `/media/images/schema/${borderColorToImage[key]}`;
    }
  }

  // Предзагрузка изображения подпятника
  const podpImg = new Image();
  podpImg.src = '/media/images/schema/podp.png';

  // Предзагрузка изображений комплектаций из справочника
  const kitDataElements = document.querySelectorAll('#kit-variant-data > div');
  for (const element of kitDataElements) {
    const imagePath = element.dataset.kitImage;
    if (imagePath) {
      const img = new Image();
      img.src = imagePath;
    }
  }
}

/**
 * Обновление конфигурации при изменении параметров.
 *
 * @param {string} kitCode Код выбранной комплектации
 */
function updateConfig(kitCode) {
  // Если kitCode не передан, берем из выбранного радио
  if (!kitCode) {
    const selectedKit = document.querySelector('input[name="selected_kit"]:checked');
    if (selectedKit) {
      kitCode = selectedKit.value;
    } else {
      kitCode = 'salon'; // По умолчанию
    }
  }

  // Отмечаем выбранный вариант как активный
  const radioButtons = document.querySelectorAll('input[name="selected_kit"]');
  radioButtons.forEach(radio => {
    const label = radio.closest('.kit-option-label');
    if (radio.value === kitCode) {
      label.classList.add('active');
      radio.checked = true;
    } else {
      label.classList.remove('active');
    }
  });

  // Обновляем изображение комплектации
  updateKitImage(kitCode);

  // Обновляем подпятник
  updatePodp();

  // Обновляем цену
  updatePrice();

  // Обновляем скрытые поля для форм
  updateHiddenFields();
}

/**
 * Обновление изображения комплектации.
 *
 * @param {string} kitCode Код выбранной комплектации
 */
function updateKitImage(kitCode) {
  console.log("Обновление изображения комплектации:", kitCode);

  // Находим данные о выбранной комплектации в скрытых полях
  const kitData = document.querySelector(`#kit-variant-data div[data-kit-code="${kitCode}"]`);
  if (!kitData) {
    console.error("Данные о комплектации не найдены:", kitCode);
    return;
  }

  // Получаем URL изображения из данных комплектации
  const imageUrl = kitData.dataset.kitImage;

  // Обновляем базовое изображение комплектации
  const kitBaseImage = document.querySelector('.kit-base-image');
  if (kitBaseImage) {
    if (imageUrl) {
      // Устанавливаем изображение из справочника
      kitBaseImage.src = imageUrl;
      console.log(`Установлено изображение комплектации: ${imageUrl}`);
    } else {
      // Если изображения нет в справочнике, используем резервное
      const fallbackImage = kitToSchemaImage[kitCode] || "salon.png";
      kitBaseImage.src = `/media/images/schema/${fallbackImage}`;
      console.log(`Установлено резервное изображение комплектации: ${fallbackImage}`);
    }
  } else {
    console.error("Элемент базового изображения комплектации не найден");
  }
}

/**
 * Обновление отображения подпятника.
 */
function updatePodp() {
  const podpElement = document.querySelector('.podpicon');
  const podpCheck = document.getElementById('podp_check');

  if (podpElement && podpCheck) {
    podpElement.style.display = podpCheck.checked ? 'block' : 'none';
    console.log("Подпятник " + (podpCheck.checked ? "показан" : "скрыт"));
  }
}

/**
 * Обновление цены при изменении комплектации и опций.
 */
function updatePrice() {
  // Базовая цена продукта
  const basePrice = parseFloat(document.querySelector('meta[name="product-price"]').content) || 0;

  // Цена выбранной комплектации
  let kitPrice = 0;
  const selectedKit = document.querySelector('input[name="selected_kit"]:checked');
  if (selectedKit) {
    const kitData = document.querySelector(`#kit-variant-data div[data-kit-code="${selectedKit.value}"]`);
    if (kitData && kitData.dataset.kitPrice) {
      kitPrice = parseFloat(kitData.dataset.kitPrice);
    }
  }

  // Цена подпятника
  let podpPrice = 0;
  if (document.getElementById('podp_check').checked) {
    const podpData = document.querySelector('#kit-variant-data div[data-option-code="podpyatnik"]');
    if (podpData && podpData.dataset.optionPrice) {
      podpPrice = parseFloat(podpData.dataset.optionPrice);
    } else {
      podpPrice = 15; // Значение по умолчанию
    }
  }

  // Итоговая цена
  const totalPrice = basePrice + kitPrice + podpPrice;

  // Обновляем отображение
  const priceElement = document.getElementById('totalPrice');
  if (priceElement) {
    priceElement.textContent = `₹${totalPrice.toFixed(2)} руб.`;
  }
}

/**
 * Обновление скрытых полей для форм.
 */
function updateHiddenFields() {
  // Получаем выбранную комплектацию
  const selectedKit = document.querySelector('input[name="selected_kit"]:checked');
  const kitCode = selectedKit ? selectedKit.value : 'salon';

  // Получаем выбранные цвета
  const carpetColor = document.getElementById('carpet_color_input').value;
  const borderColor = document.getElementById('border_color_input').value;

  // Проверяем подпятник
  const hasPodp = document.getElementById('podp_check').checked ? "1" : "0";

  // Получаем количество
  const quantity = document.getElementById('quantity').value || "1";

  // Обновляем поля формы добавления в избранное
  document.getElementById('wishlist-kit').value = kitCode;
  document.getElementById('wishlist-carpet-color').value = carpetColor;
  document.getElementById('wishlist-border-color').value = borderColor;
  document.getElementById('wishlist-podp').value = hasPodp;
  document.getElementById('wishlist-quantity').value = quantity;

  // Обновляем поля формы добавления в корзину
  document.getElementById('cart-kit').value = kitCode;
  document.getElementById('cart-carpet-color').value = carpetColor;
  document.getElementById('cart-border-color').value = borderColor;
  document.getElementById('cart-podp').value = hasPodp;
  document.getElementById('cart-quantity').value = quantity;
}

/**
 * Активация выбранного цвета.
 *
 * @param {HTMLElement} element Элемент цвета
 * @param {string} type Тип цвета ("carpet" или "border")
 */
function activateColor(element, type) {
  // Удаляем класс active со всех цветов этого типа
  const colorItems = document.querySelectorAll(`.color-picker[data-color-type="${type}"] .color-item`);
  colorItems.forEach(item => {
    item.classList.remove('active');
    item.style.border = '2px solid #ccc';
  });

  // Добавляем класс active на выбранный цвет
  element.classList.add('active');
  element.style.border = '2px solid #FFEB3B';

  // Обновляем скрытое поле с выбранным цветом
  if (type === 'carpet') {
    document.getElementById('carpet_color_input').value = element.dataset.colorId;
  } else if (type === 'border') {
    document.getElementById('border_color_input').value = element.dataset.colorId;
  }

  // Обновляем изображение коврика/окантовки
  setAttrValue(parseInt(element.dataset.attrId), parseInt(element.dataset.attrValue));

  // Обновляем скрытые поля для форм
  updateHiddenFields();
}

/**
 * Установка атрибутов и обновление изображений.
 *
 * @param {number} id ID атрибута (1=коврик, 2=окантовка, 7=подпятник)
 * @param {number} value Значение атрибута
 */
function setAttrValue(id, value) {
  console.log("setAttrValue called with id:", id, "value:", value);

  // Соответствие цветов и изображений
  if (id === attributeIds.CARPET_COLOR) {
    // Цвет коврика
    const carpetElement = document.querySelector('.matcolor');
    if (carpetElement) {
      // Проверяем, что выбрано корректное значение (1-10)
      if (value < 1 || value > 10) {
        console.error(`Некорректное значение цвета коврика: ${value}. Допустимые значения: 1-10`);
        value = 1; // Устанавливаем значение по умолчанию
      }

      // Устанавливаем изображение коврика с проверкой
      setImageWithFallback(
        carpetElement,
        `/media/images/schema/sota${value}.png`,
        '/media/images/schema/sota1.png'
      );

      console.log(`Установлено изображение коврика: sota${value}.png (${carpetColors[value] || 'Неизвестный цвет'})`);
    } else {
      console.error("Элемент коврика не найден!");
    }
  }

  if (id === attributeIds.BORDER_COLOR) {
    const borderElement = document.querySelector('.bordercolor');
    if (borderElement) {
      // Используем соответствие из таблицы или дефолтное изображение, если соответствия нет
      const borderImageFile = borderColorToImage[value] || "border211.png";

      // Устанавливаем изображение окантовки с проверкой
      setImageWithFallback(
        borderElement,
        `/media/images/schema/${borderImageFile}`,
        '/media/images/schema/border211.png'
      );

      console.log("Установлено изображение окантовки:", borderImageFile, "для цвета #", value);
    } else {
      console.error("Элемент окантовки не найден!");
    }
  }

  if (id === attributeIds.PODPYATNIK) {
    // Этот код теперь в функции updatePodp()
    updatePodp();
  }
}

/**
 * Обновление главного изображения продукта.
 *
 * @param {string} src Путь к изображению
 */
function updateMainImage(src) {
  const mainImage = document.getElementById("mainImage");
  if (mainImage) {
    mainImage.src = src;
    // Сбрасываем зум при смене изображения
    mainImage.classList.remove("zoomed-in");
  }
}

/**
 * Установка URL действия для формы удаления отзыва.
 *
 * @param {string} actionUrl URL для удаления отзыва
 */
function setDeleteAction(actionUrl) {
  const deleteForm = document.getElementById("deleteReviewForm");
  if (deleteForm) {
    deleteForm.action = actionUrl;
  }
}

/**
 * Отправка лайка для отзыва.
 *
 * @param {string} reviewId ID отзыва
 */
function toggleLike(reviewId) {
  const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

  fetch(`/product/like-review/${reviewId}/`, {
    method: "POST",
    headers: { "X-CSRFToken": csrfToken },
  })
    .then((response) => response.json())
    .then((data) => {
      const likeElement = document.getElementById(`like-count-${reviewId}`);
      const dislikeElement = document.getElementById(`dislike-count-${reviewId}`);
      if (likeElement && dislikeElement) {
        likeElement.innerText = data.likes;
        dislikeElement.innerText = data.dislikes;
      } else {
        console.error("Like or Dislike element not found in DOM.");
      }
    })
    .catch((error) => console.error("Error:", error));
}

/**
 * Отправка дизлайка для отзыва.
 *
 * @param {string} reviewId ID отзыва
 */
function toggleDislike(reviewId) {
  const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

  fetch(`/product/dislike-review/${reviewId}/`, {
    method: "POST",
    headers: { "X-CSRFToken": csrfToken },
  })
    .then((response) => response.json())
    .then((data) => {
      const likeElement = document.getElementById(`like-count-${reviewId}`);
      const dislikeElement = document.getElementById(`dislike-count-${reviewId}`);
      if (likeElement && dislikeElement) {
        likeElement.innerText = data.likes;
        dislikeElement.innerText = data.dislikes;
      } else {
        console.error("Like or Dislike element not found in DOM.");
      }
    })
    .catch((error) => console.error("Error:", error));
}

/**
 * Проверка существования изображения.
 *
 * @param {string} url URL изображения
 * @param {Function} successCallback Функция, вызываемая при успешной загрузке
 * @param {Function} errorCallback Функция, вызываемая при ошибке загрузки
 */
function checkImageExists(url, successCallback, errorCallback) {
  const img = new Image();
  img.onload = successCallback;
  img.onerror = errorCallback;
  img.src = url;
}

/**
 * Установка изображения с запасным вариантом.
 *
 * @param {HTMLElement} element Элемент изображения
 * @param {string} primarySrc Основной источник
 * @param {string} fallbackSrc Запасной источник
 */
function setImageWithFallback(element, primarySrc, fallbackSrc) {
  if (!primarySrc) {
    element.src = fallbackSrc;
    return;
  }

  checkImageExists(
    primarySrc,
    function() { element.src = primarySrc; },
    function() {
      console.warn(`Изображение ${primarySrc} не найдено, используется запасной вариант`);
      element.src = fallbackSrc;
    }
  );
}

/**
 * Улучшение взаимодействия с горизонтальной прокруткой.
 */
function initColorPickerScrolls() {
  const colorPickers = document.querySelectorAll('.color-picker');

  colorPickers.forEach(picker => {
    // Показываем индикатор прокрутки, только если контент не помещается
    if (picker.scrollWidth > picker.clientWidth) {
      const indicator = picker.nextElementSibling;
      if (indicator && indicator.classList.contains('scroll-indicator')) {
        indicator.style.display = 'flex';
      }
    }

    // Индикатор прокрутки левого и правого края
    picker.addEventListener('scroll', function() {
      const isAtStart = this.scrollLeft <= 10;
      const isAtEnd = this.scrollLeft + this.clientWidth >= this.scrollWidth - 10;

      const indicator = this.nextElementSibling;
      if (indicator && indicator.classList.contains('scroll-indicator')) {
        const leftArrow = indicator.querySelector('.fa-chevron-left');
        const rightArrow = indicator.querySelector('.fa-chevron-right');

        if (leftArrow) leftArrow.style.opacity = isAtStart ? '0.3' : '1';
        if (rightArrow) rightArrow.style.opacity = isAtEnd ? '0.3' : '1';
      }
    });
  });
}

/**
 * Инициализация зума для главного изображения.
 */
function initializeImageZoom() {
  const mainImage = document.getElementById('mainImage');
  if (mainImage) {
    mainImage.addEventListener('click', function() {
      this.classList.toggle('zoomed-in');
    });
  }
}

/**
 * Инициализация кнопок для изменения количества товара.
 */
function initializeQuantityButtons() {
  const quantityInput = document.getElementById('quantity');
  const plusButton = document.getElementById('button-plus');
  const minusButton = document.getElementById('button-minus');

  if (quantityInput && plusButton && minusButton) {
    plusButton.addEventListener('click', function() {
      let quantity = parseInt(quantityInput.value);
      if (isNaN(quantity)) quantity = 0;
      quantityInput.value = quantity + 1;
      updateHiddenFields();
    });

    minusButton.addEventListener('click', function() {
      let quantity = parseInt(quantityInput.value);
      if (isNaN(quantity) || quantity <= 1) quantity = 2;
      quantityInput.value = quantity - 1;
      updateHiddenFields();
    });

    quantityInput.addEventListener('change', function() {
      let quantity = parseInt(quantityInput.value);
      if (isNaN(quantity) || quantity < 1) {
        quantityInput.value = 1;
      }
      updateHiddenFields();
    });
  }
}

/**
 * Инициализация функциональности страницы продукта.
 */
document.addEventListener("DOMContentLoaded", function () {
  console.log("DOM загружен. Инициализация страницы продукта...");

  // Предзагрузка изображений
  preloadImages();

  // Инициализация скроллеров для выбора цвета
  initColorPickerScrolls();

  // Инициализация масштабирования изображения
  initializeImageZoom();

  // Инициализация кнопок изменения количества
  initializeQuantityButtons();

  // Инициализация конфигурации по умолчанию (используем первую комплектацию)
  updateConfig();
});