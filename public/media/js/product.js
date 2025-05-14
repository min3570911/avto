/**
 * product.js - Скрипт для страницы продукта с визуализацией ковриков
 *
 * Функциональность:
 * - Визуализация ковриков с разными цветами и окантовкой
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
}

/**
 * Получение корректной цены при выборе размера.
 *
 * @param {string} selected_size Выбранный размер
 */
function get_correct_price(selected_size) {
  const urlParams = new URLSearchParams(window.location.search);
  urlParams.set("size", selected_size);
  window.location.search = urlParams.toString();
}

/**
 * Обновление главного изображения продукта.
 *
 * @param {string} src Путь к изображению
 */
function updateMainImage(src) {
  document.getElementById("mainImage").src = src;
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

      // Устанавливаем изображение коврика
      carpetElement.src = `/media/images/schema/sota${value}.png`;
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
      borderElement.src = `/media/images/schema/${borderImageFile}`;
      console.log("Установлено изображение окантовки:", borderElement.src, "для цвета #", value);
    } else {
      console.error("Элемент окантовки не найден!");
    }
  }

  if (id === attributeIds.PODPYATNIK) {
    // Подпятник
    const podpElement = document.querySelector('.podpicon');
    if (podpElement) {
      podpElement.style.display = value == 1 ? 'block' : 'none';
      console.log("Подпятник " + (value == 1 ? "показан" : "скрыт"));
    } else {
      console.error("Элемент подпятника не найден!");
    }
  }

  // Обновляем URL кнопки "Добавить в корзину"
  updateCartUrl();
}

/**
 * Обновление URL для кнопки добавления в корзину.
 */
function updateCartUrl() {
  const cartBtn = document.getElementById('add-to-cart-btn');
  if (!cartBtn) return;

  let href = cartBtn.getAttribute('href');
  const carpetColor = document.getElementById('carpet_color_input')?.value || '';
  const borderColor = document.getElementById('border_color_input')?.value || '';
  const hasPodp = document.getElementById('podp_check')?.checked ? '1' : '0';

  // Заменяем плейсхолдеры на фактические значения
  href = href.replace('__carpet_color__', carpetColor);
  href = href.replace('__border_color__', borderColor);

  // Обновляем значение подпятника
  href = href.replace(/podp=\d/, `podp=${hasPodp}`);

  console.log("Обновленный URL корзины:", href);
  cartBtn.setAttribute('href', href);
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
  checkImageExists(
    primarySrc,
    function() { element.src = primarySrc; },
    function() {
      console.warn(`Изображение ${primarySrc} не найдено, используется запасной вариант`);
      element.src = fallbackSrc;
    }
  );
}

// Улучшение взаимодействия с горизонтальной прокруткой
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
 * Инициализация функциональности страницы продукта.
 */
document.addEventListener("DOMContentLoaded", function () {
  console.log("DOM загружен. Инициализация страницы продукта...");
  console.log("Доступные цвета ковриков:", Object.entries(carpetColors).map(([key, value]) => `${key}: ${value}`).join(', '));

  // Проверяем наличие необходимых элементов в DOM
  console.log("Элемент коврика:", document.querySelector('.matcolor'));
  console.log("Элемент окантовки:", document.querySelector('.bordercolor'));
  console.log("Элемент подпятника:", document.querySelector('.podpicon'));

  // Предзагрузка изображений
  preloadImages();

  // Инициализация скроллеров
  initColorPickerScrolls();

  // Эффект зума для главного изображения
  const mainImage = document.getElementById("mainImage");
  if (mainImage) {
    mainImage.addEventListener("click", function () {
      if (mainImage.classList.contains("zoomed-in")) {
        mainImage.classList.remove("zoomed-in");
      } else {
        mainImage.classList.add("zoomed-in");
      }
    });
  }

  // Инициализация выбора цветов
  const colorPickers = document.querySelectorAll('.color-picker');

  colorPickers.forEach(picker => {
    // Находим все кружки цветов в текущем пикере
    const colorItems = picker.querySelectorAll('.color-item');
    const colorType = picker.dataset.colorType;
    const inputField = document.getElementById(`${colorType}_color_input`);

    // Проверяем корректность количества цветов
    if (colorType === 'carpet' && colorItems.length !== 10) {
      console.warn(`Внимание! Количество кружков цвета коврика (${colorItems.length}) не соответствует ожидаемому (10).`);
    }

    colorItems.forEach(item => {
      item.addEventListener('click', function() {
        const attrValue = parseInt(this.dataset.attrValue);
        const colorName = this.getAttribute('title');

        console.log(`Выбран ${colorType} цвет #${attrValue}: ${colorName}`);

        // Сбросить активный класс у всех элементов
        colorItems.forEach(i => i.classList.remove('active'));

        // Добавить активный класс к выбранному
        this.classList.add('active');

        // Обновить скрытое поле
        if (inputField) {
          inputField.value = this.dataset.colorId;
        }

        // Обновить изображение коврика/окантовки
        setAttrValue(parseInt(this.dataset.attrId), attrValue);
      });
    });
  });

  // Обработчик для подпятника
  const podpCheck = document.getElementById('podp_check');
  if (podpCheck) {
    podpCheck.addEventListener('change', function() {
      console.log("Переключение подпятника:", this.checked);
      setAttrValue(parseInt(this.dataset.attrId), this.checked ? parseInt(this.dataset.attrValue) : 0);
    });
  }

  // Инициализация URL при загрузке страницы
  updateCartUrl();
});