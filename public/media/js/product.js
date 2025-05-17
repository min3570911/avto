/**
 * Скрипт для управления цветом ковриков и окантовки, а также выбором комплектации
 *
 * Данные о комплектациях, ценах и изображениях берутся динамически из DOM,
 * куда они передаются из Django-бэкенда
 */

// 🎨 Таблица цветов ковриков
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

// 🎨 Таблица цветов окантовки
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

/**
 * Получает данные о комплектациях и ценах из DOM
 * @returns {Object} Справочник комплектаций
 */
function getKitVariantsFromDOM() {
  const kitVariants = {};

  // Находим все доступные комплектации в DOM
  const kitElements = document.querySelectorAll('input[name="selected_kit"]');

  kitElements.forEach(kitElement => {
    const kitCode = kitElement.value;
    const kitLabel = kitElement.closest('.kit-option-label');

    if (kitLabel) {
      // Получаем название из текста лейбла
      const nameMatch = kitLabel.textContent.match(/^(.*?)\s+\(/);
      const name = nameMatch ? nameMatch[1].trim() : kitLabel.textContent.trim();

      // Получаем цену из текста лейбла
      const priceMatch = kitLabel.textContent.match(/\+(\d+(?:\.\d+)?)\s*руб\./);
      const price = priceMatch ? parseFloat(priceMatch[1]) : 0;

      // Путь к изображению берем из скрытого элемента с данными комплектаций
      const kitDataElement = document.querySelector(`#kit-variant-data div[data-kit-code="${kitCode}"]`);
      let image = '/media/images/schema/salon.png'; // Значение по умолчанию

      if (kitDataElement && kitDataElement.dataset.kitImage) {
        image = kitDataElement.dataset.kitImage;
      }

      // Сохраняем данные в справочник
      kitVariants[kitCode] = {
        name: name,
        image: image,
        price: price
      };
    }
  });

  return kitVariants;
}

/**
 * Получает данные о дополнительных опциях из DOM
 * @returns {Object} Справочник опций
 */
function getOptionVariantsFromDOM() {
  const optionVariants = {};

  // Находим опцию подпятника
  const podpElement = document.getElementById('podp_check');
  if (podpElement) {
    const podpLabel = podpElement.closest('.form-check').querySelector('label');

    if (podpLabel) {
      // Получаем цену из текста лейбла
      const priceMatch = podpLabel.textContent.match(/\+(\d+(?:\.\d+)?)\s*руб\./);
      const price = priceMatch ? parseFloat(priceMatch[1]) : 15.00; // Цена по умолчанию, если не удалось извлечь

      // Сохраняем данные в справочник
      optionVariants['podpyatnik'] = {
        name: 'Подпятник',
        price: price
      };
    }
  }

  return optionVariants;
}

/**
 * Инициализирует область выбора комплектации
 * Создает контейнер с изображением схемы рядом с радио-кнопками
 */
function initializeConfigSection() {
  // Находим контейнер с комплектациями
  const configSection = document.querySelector('.form-group:has(label:contains("Комплектация"))');
  if (!configSection) return;

  // Создаем контейнер для схемы комплектации
  const schemaContainer = document.createElement('div');
  schemaContainer.className = 'kit-schema-container';
  schemaContainer.style.cssText = 'display: flex; flex-direction: row; margin-top: 15px;';

  // Создаем контейнер для радио-кнопок
  const radioContainer = document.createElement('div');
  radioContainer.className = 'kit-radio-options';
  radioContainer.style.cssText = 'flex: 1;';

  // Перемещаем все существующие радио-кнопки в новый контейнер
  const kitOptions = configSection.querySelector('.kit-options');
  if (kitOptions) {
    radioContainer.appendChild(kitOptions);
  }

  // Создаем контейнер для изображения схемы
  const imageContainer = document.createElement('div');
  imageContainer.className = 'kit-image-container';
  imageContainer.style.cssText = 'flex: 1; text-align: center; margin-left: 15px;';

  // Создаем изображение схемы
  const schemaImage = document.createElement('img');
  schemaImage.id = 'kit-schema-image';
  schemaImage.className = 'kit-schema-image';
  schemaImage.style.cssText = 'max-width: 100%; max-height: 200px; border: 1px solid #ddd; border-radius: 4px;';
  schemaImage.alt = 'Схема комплектации';

  // Добавляем изображение в контейнер
  imageContainer.appendChild(schemaImage);

  // Собираем все вместе
  schemaContainer.appendChild(radioContainer);
  schemaContainer.appendChild(imageContainer);

  // Добавляем собранный контейнер в раздел комплектации
  configSection.appendChild(schemaContainer);

  // Загружаем изображение для комплектации по умолчанию
  const defaultKitCode = 'salon';
  const selectedKit = document.querySelector('input[name="selected_kit"]:checked');
  if (selectedKit) {
    updateSchemaImage(selectedKit.value);
  } else {
    updateSchemaImage(defaultKitCode);
  }
}

/**
 * Обновляет изображение схемы комплектации
 * @param {string} kitCode - Код выбранной комплектации
 */
function updateSchemaImage(kitCode) {
  const schemaImage = document.getElementById('kit-schema-image');
  if (!schemaImage) return;

  // Получаем данные о комплектациях из DOM
  const kitVariants = getKitVariantsFromDOM();

  // Берем изображение из данных комплектации
  if (kitVariants[kitCode] && kitVariants[kitCode].image) {
    schemaImage.src = kitVariants[kitCode].image;
    schemaImage.alt = `Схема комплектации "${kitVariants[kitCode].name}"`;
  } else {
    // Если изображения нет, берем из data-атрибута или показываем заглушку
    const kitDataElement = document.querySelector(`#kit-variant-data div[data-kit-code="${kitCode}"]`);
    if (kitDataElement && kitDataElement.dataset.kitImage) {
      schemaImage.src = kitDataElement.dataset.kitImage;
    } else {
      schemaImage.src = '/media/images/schema/salon.png';
    }
    schemaImage.alt = 'Схема комплектации';
  }
}

/**
 * Активирует выбор комплектации
 * @param {string} kitCode - Код выбранной комплектации
 */
function updateConfig(kitCode) {
  // Если код не передан, берем активный
  if (!kitCode) {
    const selectedKit = document.querySelector('input[name="selected_kit"]:checked');
    kitCode = selectedKit ? selectedKit.value : 'salon';
  }

  // Активируем выбранную комплектацию визуально
  const labels = document.querySelectorAll('.kit-option-label');
  labels.forEach(label => {
    const radio = label.querySelector('input[type="radio"]');
    if (radio && radio.value === kitCode) {
      label.classList.add('active');
      radio.checked = true;
    } else {
      label.classList.remove('active');
    }
  });

  // Обновляем изображение схемы комплектации в секции выбора комплектации
  updateSchemaImage(kitCode);

  // Обновляем изображение схемы в визуализаторе ковриков
  const kitImage = document.querySelector('.kit-base-image');
  if (kitImage) {
    const kitDataElement = document.querySelector(`#kit-variant-data div[data-kit-code="${kitCode}"]`);
    if (kitDataElement && kitDataElement.dataset.kitImage) {
      kitImage.src = kitDataElement.dataset.kitImage;
    }
  }

  // Обновляем цену
  updatePrice();

  // Обновляем скрытые поля форм
  updateHiddenFields();
}

/**
 * Активирует выбранный цвет и обновляет изображение
 * @param {HTMLElement} element - Элемент с цветом, на который кликнули
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
      borderImage.src = `/media/images/schema/${borderColorToImage[attrValue]}`;
    }
  }

  // Обновляем скрытые поля форм
  updateHiddenFields();
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
 * Обновляет цену на основе выбранной комплектации и опций
 */
function updatePrice() {
  // Получаем данные о комплектациях из DOM
  const kitVariants = getKitVariantsFromDOM();
  const optionVariants = getOptionVariantsFromDOM();

  // Берем выбранную комплектацию
  const selectedKit = document.querySelector('input[name="selected_kit"]:checked');
  const kitCode = selectedKit ? selectedKit.value : 'salon';

  let totalPrice = 0;

  // Добавляем цену комплектации
  if (kitVariants[kitCode]) {
    totalPrice = kitVariants[kitCode].price;
  }

  // Добавляем цену подпятника, если выбран
  const podpCheck = document.getElementById('podp_check');
  if (podpCheck && podpCheck.checked && optionVariants['podpyatnik']) {
    totalPrice += optionVariants['podpyatnik'].price;
  }

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
  const carpetColor = document.getElementById('carpet_color_input').value;
  const borderColor = document.getElementById('border_color_input').value;
  const hasPodp = document.getElementById('podp_check').checked ? "1" : "0";
  const quantity = document.getElementById('quantity').value || "1";
  const selectedKit = document.querySelector('input[name="selected_kit"]:checked');
  const kitCode = selectedKit ? selectedKit.value : 'salon';


  // Обновляем скрытые поля формы избранного
  document.getElementById('wishlist-kit').value = kitCode;
  document.getElementById('wishlist-carpet-color').value = carpetColor;
  document.getElementById('wishlist-border-color').value = borderColor;
  document.getElementById('wishlist-podp').value = hasPodp;
  document.getElementById('wishlist-quantity').value = quantity;

  // Обновляем скрытые поля формы корзины
  document.getElementById('cart-kit').value = kitCode;
  document.getElementById('cart-carpet-color').value = carpetColor;
  document.getElementById('cart-border-color').value = borderColor;
  document.getElementById('cart-podp').value = hasPodp;
  document.getElementById('cart-quantity').value = quantity;
}
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
  // Инициализируем секцию выбора комплектации с изображением схемы
  initializeConfigSection();

  // Инициализируем комплектацию (берем активную или устанавливаем по умолчанию)
  const selectedKit = document.querySelector('input[name="selected_kit"]:checked');
  if (selectedKit) {
    updateConfig(selectedKit.value);
  } else {
    updateConfig('salon');
  }

  // Привязываем обработчики событий для выбора цвета
  const colorItems = document.querySelectorAll('.color-item');
  colorItems.forEach(item => {
    const type = item.closest('.color-picker').dataset.colorType;
    item.addEventListener('click', function() {
      activateColor(this, type);
    });
  });

  // Привязываем обработчики событий для выбора комплектации
  const kitRadios = document.querySelectorAll('input[name="selected_kit"]');
  kitRadios.forEach(radio => {
    radio.addEventListener('change', function() {
      updateConfig(this.value);
    });
  });

  // Привязываем обработчик для подпятника
  const podpCheck = document.getElementById('podp_check');
  if (podpCheck) {
    podpCheck.addEventListener('change', updatePodp);
  }
});

  // Обновляем скрытые поля формы избранного
  document.getElementById('wishlist-kit').value = kitCode;
  document.getElementById('wishlist-carpet-color').value = carpetColor;
  document.getElementById('wishlist-border-color').value = borderColor;
  document.getElementById('wishlist-podp').value = hasPodp;
  document.getElementById('wishlist-quantity').value = quantity;

  // Обновляем скрытые поля формы корзины
  document.getElementById('cart-kit').value = kitCode;
  document.getElementById('cart-carpet-color').value = carpetColor;
  document.getElementById('cart-border-color').value = borderColor;
  document.getElementById('cart-podp').value = hasPodp;
  document.getElementById('cart-quantity').value = quantity;
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
  // Инициализируем секцию выбора комплектации с изображением схемы
  initializeConfigSection();

  // Инициализируем комплектацию по умолчанию (Салон)
  updateConfig('salon');

  // Привязываем обработчики событий для выбора цвета
  const colorItems = document.querySelectorAll('.color-item');
  colorItems.forEach(item => {
    const type = item.closest('.color-picker').dataset.colorType;
    item.addEventListener('click', function() {
      activateColor(this, type);
    });
  });

  // Привязываем обработчики событий для выбора комплектации
  const kitRadios = document.querySelectorAll('input[name="selected_kit"]');
  kitRadios.forEach(radio => {
    radio.addEventListener('change', function() {
      updateConfig(this.value);
    });
  });

  // Привязываем обработчик для подпятника
  const podpCheck = document.getElementById('podp_check');
  if (podpCheck) {
    podpCheck.addEventListener('change', updatePodp);
  }
});