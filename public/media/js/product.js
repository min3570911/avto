/**
 * Скрипт для управления цветом ковриков и окантовки, а также выбором комплектации
 */

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
  // Перемещаем изображение схемы к радио-кнопкам и скрываем в визуализаторе
  moveKitSchemaImage();

  // Инициализируем начальный выбор комплектации
  const selectedKit = document.querySelector('input[name="selected_kit"]:checked');
  if (selectedKit) {
    updateConfig(selectedKit.value);
  } else {
    updateConfig('salon');
  }

  // Инициализируем обработчики событий
  setupEventHandlers();
});

/**
 * Перемещает изображение схемы комплектации рядом с радио-кнопками и скрывает в визуализаторе
 */
function moveKitSchemaImage() {
  // Находим контейнер с комплектациями
  const kitConfigSection = document.getElementById('kit-configuration');
  if (!kitConfigSection) return;

  // Находим контейнер с радио-кнопками
  const kitOptions = kitConfigSection.querySelector('.kit-options');
  if (!kitOptions) return;

  // Находим изображение схемы в визуализаторе
  const visualizerImage = document.querySelector('.kit-base-image');

  // Скрываем изображение в визуализаторе (оставляем только слои с ковриком и окантовкой)
  if (visualizerImage) {
    visualizerImage.style.display = 'none';
  }

  // Создаем флекс-контейнер для радио-кнопок и изображения
  const flexContainer = document.createElement('div');
  flexContainer.style.cssText = 'display: flex; flex-wrap: wrap; gap: 20px; margin-bottom: 15px;';

  // Вставляем флекс-контейнер перед kitOptions
  kitOptions.parentNode.insertBefore(flexContainer, kitOptions);

  // Перемещаем kitOptions внутрь флекс-контейнера
  flexContainer.appendChild(kitOptions);

  // Добавляем стили к контейнеру с радио-кнопками
  kitOptions.style.cssText = 'flex: 1; min-width: 200px;';

  // Создаем контейнер для изображения
  const imageContainer = document.createElement('div');
  imageContainer.style.cssText = 'flex: 1; min-width: 150px; max-width: 250px; text-align: center; border: 1px solid #ddd; border-radius: 4px; padding: 10px; background-color: #f8f8f8;';

  // Создаем изображение схемы
  const schemaImage = document.createElement('img');
  schemaImage.id = 'kit-schema-image';
  schemaImage.style.cssText = 'max-width: 100%; height: auto;';
  schemaImage.alt = 'Схема комплектации';

  // Получаем URL изображения из существующего элемента или из data-атрибутов
  let imageUrl = '';
  if (visualizerImage && visualizerImage.src) {
    imageUrl = visualizerImage.src;
  } else {
    // Ищем выбранную комплектацию
    const selectedKit = document.querySelector('input[name="selected_kit"]:checked');
    const kitCode = selectedKit ? selectedKit.value : 'salon';

    // Получаем изображение из data-атрибутов
    const kitData = document.querySelector(`#kit-variant-data div[data-kit-code="${kitCode}"]`);
    if (kitData && kitData.dataset.kitImage) {
      imageUrl = kitData.dataset.kitImage;
    }
  }

  // Устанавливаем изображение схемы
  if (imageUrl) {
    schemaImage.src = imageUrl;
  }

  // Добавляем изображение в контейнер
  imageContainer.appendChild(schemaImage);
  flexContainer.appendChild(imageContainer);
}

/**
 * Устанавливает обработчики событий для интерактивных элементов
 */
function setupEventHandlers() {
  // Обработчики для выбора комплектации
  const kitRadios = document.querySelectorAll('input[name="selected_kit"]');
  kitRadios.forEach(radio => {
    radio.addEventListener('change', function() {
      updateConfig(this.value);
    });
  });

  // Обработчик для подпятника
  const podpCheck = document.getElementById('podp_check');
  if (podpCheck) {
    podpCheck.addEventListener('change', updatePodp);
  }

  // Обработчики для выбора цвета
  const colorItems = document.querySelectorAll('.color-item');
  colorItems.forEach(item => {
    const colorPicker = item.closest('.color-picker');
    if (colorPicker && colorPicker.dataset.colorType) {
      const type = colorPicker.dataset.colorType;
      item.addEventListener('click', function() {
        activateColor(this, type);
      });
    }
  });

  // Обработчики для кнопок количества
  const plusBtn = document.getElementById('button-plus');
  const minusBtn = document.getElementById('button-minus');
  const quantityInput = document.getElementById('quantity');

  if (plusBtn && quantityInput) {
    plusBtn.addEventListener('click', function() {
      quantityInput.value = parseInt(quantityInput.value || '1') + 1;
      updateHiddenFields();
    });
  }

  if (minusBtn && quantityInput) {
    minusBtn.addEventListener('click', function() {
      const currentVal = parseInt(quantityInput.value || '1');
      if (currentVal > 1) {
        quantityInput.value = currentVal - 1;
        updateHiddenFields();
      }
    });
  }

  // Добавляем обработчик клика для зума изображения
  const mainImage = document.getElementById('mainImage');
  if (mainImage) {
    mainImage.addEventListener('click', function() {
      this.classList.toggle('zoomed-in');
    });
  }
}

/**
 * Обновляет конфигурацию при выборе комплектации
 * @param {string} kitCode - Код выбранной комплектации
 */
function updateConfig(kitCode) {
  // Выделяем выбранную комплектацию
  const kitLabels = document.querySelectorAll('.kit-option-label');
  kitLabels.forEach(label => {
    const radio = label.querySelector('input[type="radio"]');
    if (radio && radio.value === kitCode) {
      label.classList.add('active');
      radio.checked = true;
    } else {
      label.classList.remove('active');
    }
  });

  // Обновляем изображение схемы рядом с радио-кнопками
  updateKitSchemaImage(kitCode);

  // Обновляем цену и скрытые поля
  updatePrice();
  updateHiddenFields();
}

/**
 * Обновляет изображение схемы комплектации
 * @param {string} kitCode - Код выбранной комплектации
 */
function updateKitSchemaImage(kitCode) {
  // Находим изображение схемы
  const schemaImage = document.getElementById('kit-schema-image');
  if (!schemaImage) return;

  // Находим data-атрибуты выбранной комплектации
  const kitData = document.querySelector(`#kit-variant-data div[data-kit-code="${kitCode}"]`);
  if (!kitData) return;

  // Получаем URL изображения из data-атрибута
  if (kitData.dataset.kitImage) {
    schemaImage.src = kitData.dataset.kitImage;
    schemaImage.alt = `Схема комплектации ${kitCode}`;
  }
}

/**
 * Обновляет отображение подпятника
 */
function updatePodp() {
  const podpElement = document.querySelector('.podpicon');
  const podpCheck = document.getElementById('podp_check');

  if (podpElement && podpCheck) {
    // Показываем/скрываем подпятник
    podpElement.style.display = podpCheck.checked ? 'block' : 'none';

    // Обновляем цену и скрытые поля
    updatePrice();
    updateHiddenFields();
  }
}

/**
 * Активирует выбранный цвет и обновляет изображение
 * @param {HTMLElement} element - Элемент цвета
 * @param {string} type - Тип цвета ('carpet' или 'border')
 */
function activateColor(element, type) {
  // Сбрасываем активное состояние всех цветов этого типа
  const colorItems = document.querySelectorAll(`.color-picker[data-color-type="${type}"] .color-item`);
  colorItems.forEach(item => {
    item.classList.remove('active');
    item.style.border = '2px solid #ccc';
  });

  // Отмечаем выбранный цвет
  element.classList.add('active');
  element.style.border = '2px solid #FFEB3B';

  // Обновляем скрытые поля
  const colorId = element.dataset.colorId;
  const attrId = parseInt(element.dataset.attrId);
  const attrValue = parseInt(element.dataset.attrValue);

  if (type === 'carpet') {
    document.getElementById('carpet_color_input').value = colorId;
  } else if (type === 'border') {
    document.getElementById('border_color_input').value = colorId;
  }

  // Обновляем изображение цвета
  if (attrId === 1) { // Цвет коврика
    const carpetImage = document.querySelector('.matcolor');
    if (carpetImage) {
      carpetImage.src = `/media/images/schema/sota${attrValue}.png`;
    }
  } else if (attrId === 2) { // Цвет окантовки
    const borderImage = document.querySelector('.bordercolor');
    if (borderImage) {
      // Используем предопределенные изображения для окантовки
      const borderImageMap = {
        1: "border211.png", 2: "border212.png", 3: "border213.png", 4: "border214.png",
        5: "border215.png", 6: "border216.png", 7: "border217.png", 8: "border218.png",
        9: "border219.png", 10: "border220.png", 11: "border221.png", 12: "border222.png",
        13: "border223.png"
      };

      const borderFile = borderImageMap[attrValue] || "border211.png";
      borderImage.src = `/media/images/schema/${borderFile}`;
    }
  }

  // Обновляем скрытые поля форм
  updateHiddenFields();
}

/**
 * Обновляет цену на основе выбранной комплектации и опций
 */
function updatePrice() {
  // Находим выбранную комплектацию
  const selectedKit = document.querySelector('input[name="selected_kit"]:checked');
  if (!selectedKit) return;

  // Находим data-атрибуты выбранной комплектации
  const kitData = document.querySelector(`#kit-variant-data div[data-kit-code="${selectedKit.value}"]`);
  if (!kitData) return;

  // Получаем базовую цену продукта из мета-тега
  let basePrice = parseFloat(document.querySelector('meta[name="product-price"]').content || 0);

  // Получаем цену модификатора комплектации из data-атрибута
  let kitPrice = parseFloat(kitData.dataset.kitPrice || 0);

  // Получаем цену подпятника, если выбран
  let podpPrice = 0;
  const podpCheck = document.getElementById('podp_check');

  if (podpCheck && podpCheck.checked) {
    // Ищем цену подпятника в data-атрибутах
    const podpData = document.querySelector('#kit-variant-data div[data-option-code="podpyatnik"]');
    if (podpData && podpData.dataset.optionPrice) {
      podpPrice = parseFloat(podpData.dataset.optionPrice);
    }
  }

  // Рассчитываем итоговую цену
  const totalPrice = basePrice + kitPrice + podpPrice;

  // Обновляем отображение цены
  const priceElement = document.getElementById('totalPrice');
  if (priceElement) {
    priceElement.textContent = `₹${totalPrice.toFixed(2)} руб.`;
  }
}

/**
 * Обновляет скрытые поля форм
 */
function updateHiddenFields() {
  // Получаем выбранные значения
  const selectedKit = document.querySelector('input[name="selected_kit"]:checked');
  const kitCode = selectedKit ? selectedKit.value : 'salon';
  const carpetColor = document.getElementById('carpet_color_input').value;
  const borderColor = document.getElementById('border_color_input').value;
  const hasPodp = document.getElementById('podp_check').checked ? '1' : '0';
  const quantity = document.getElementById('quantity').value || '1';

  // Обновляем форму добавления в избранное
  document.getElementById('wishlist-kit').value = kitCode;
  document.getElementById('wishlist-carpet-color').value = carpetColor;
  document.getElementById('wishlist-border-color').value = borderColor;
  document.getElementById('wishlist-podp').value = hasPodp;
  document.getElementById('wishlist-quantity').value = quantity;

  // Обновляем форму добавления в корзину
  document.getElementById('cart-kit').value = kitCode;
  document.getElementById('cart-carpet-color').value = carpetColor;
  document.getElementById('cart-border-color').value = borderColor;
  document.getElementById('cart-podp').value = hasPodp;
  document.getElementById('cart-quantity').value = quantity;
}

/**
 * Обновляет главное изображение продукта при клике на миниатюру
 * @param {string} src - Путь к изображению
 */
function updateMainImage(src) {
  const mainImage = document.getElementById('mainImage');
  if (mainImage) {
    mainImage.src = src;
    // Сбрасываем зум при смене изображения
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
 * Отправляет лайк для отзыва
 * @param {string} reviewId - ID отзыва
 */
function toggleLike(reviewId) {
  // Используем уже существующую функцию из шаблона
  const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

  fetch(`/product/like-review/${reviewId}/`, {
    method: 'POST',
    headers: { 'X-CSRFToken': csrfToken }
  })
  .then(response => response.json())
  .then(data => {
    document.getElementById(`like-count-${reviewId}`).innerText = data.likes;
    document.getElementById(`dislike-count-${reviewId}`).innerText = data.dislikes;
  });
}

/**
 * Отправляет дизлайк для отзыва
 * @param {string} reviewId - ID отзыва
 */
function toggleDislike(reviewId) {
  // Используем уже существующую функцию из шаблона
  const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

  fetch(`/product/dislike-review/${reviewId}/`, {
    method: 'POST',
    headers: { 'X-CSRFToken': csrfToken }
  })
  .then(response => response.json())
  .then(data => {
    document.getElementById(`like-count-${reviewId}`).innerText = data.likes;
    document.getElementById(`dislike-count-${reviewId}`).innerText = data.dislikes;
  });
}