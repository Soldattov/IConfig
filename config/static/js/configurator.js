/**
 * Конфигуратор ПК - основной JavaScript файл
 * Отвечает за:
 * 1. Управление выбором компонентов
 * 2. Фильтрацию совместимых компонентов
 * 3. Отображение превью компонентов
 * 4. Расчет общей стоимости
 */
document.addEventListener('DOMContentLoaded', function () {
    // Хранилище выбранных компонентов для проверки совместимости
    let selectedGPU = null;      // Выбранная видеокарта
    let selectedCPU = null;      // Выбранный процессор
    let selectedMotherboard = null; // Выбранная материнская плата

    /**
     * Обработчик раскрытия/сворачивания категорий компонентов
     * При клике на заголовок категории:
     * 1. Переключает состояние expanded
     * 2. Поворачивает иконку стрелки
     * 3. Анимирует высоту контента
     */
    document.querySelectorAll('.category-header').forEach(header => {
        header.addEventListener('click', function () {
            const content = this.nextElementSibling;
            const icon = this.querySelector('i');

            content.classList.toggle('expanded');
            icon.classList.toggle('rotated');

            if (content.classList.contains('expanded')) {
                content.style.maxHeight = content.scrollHeight + 'px';
            } else {
                content.style.maxHeight = '0';
            }
        });
    });

    /**
     * Обработчик выбора компонентов
     * При выборе компонента:
     * 1. Проверяет доступность компонента
     * 2. Обновляет визуальное выделение
     * 3. Показывает превью компонента
     * 4. Обновляет фильтры совместимости
     * 5. Разблокирует следующие категории
     */
    document.querySelectorAll('.component-option').forEach(option => {
        option.addEventListener('click', function () {
            if (this.classList.contains('locked') || this.classList.contains('disabled')) {
                return;
            }

            const componentType = this.dataset.component;
            const componentId = this.dataset.id;
            const componentName = this.querySelector('.component-name').textContent;
            const componentPrice = parseInt(this.querySelector('.component-price').textContent);

            // Снимаем выделение с других компонентов в категории
            this.parentNode.querySelectorAll('.component-option').forEach(el => {
                el.classList.remove('active');
            });

            this.classList.add('active');
            showComponentPreview(componentType, componentId, componentName, componentPrice);

            // Обработка выбора конкретных компонентов
            if (componentType === 'gpu') {
                selectedGPU = {
                    id: componentId,
                    power: parseInt(this.dataset.power) || 0,
                    consumption: parseInt(this.dataset.consumption) || 0,
                    size: parseInt(this.dataset.size.split('x')[0]) || 0
                };
                filterCPUs();
                filterPSU();
                filterCase();
                unlockNextCategory('cpu');
                unlockNextCategory('motherboard');
            } else if (componentType === 'cpu') {
                selectedCPU = {
                    id: componentId,
                    socket: this.dataset.socket
                };
                filterMother();
                unlockNextCategory('motherboard');
            } else if (componentType === 'motherboard') {
                selectedMotherboard = {
                    id: componentId,
                    ramType: this.dataset.ramType,
                    formFactor: this.dataset.formFactor,
                    sataSlots: parseInt(this.dataset.sataSlots) || 0
                };
                filterRAM();
                filterCooling();
                filterStorage();
                filterCase();
                unlockNextCategory('ram');
                unlockNextCategory('cooling');
                unlockNextCategory('storage');
                unlockNextCategory('case');
            }
        });
    });

    /**
     * Фильтрация процессоров на основе выбранной видеокарты
     * Показывает только процессоры с мощностью, близкой к мощности видеокарты
     */
    function filterCPUs() {
        if (!selectedGPU) return;

        const cpuOptions = document.querySelectorAll('.component-option[data-component="cpu"]');
        const gpuPower = selectedGPU.power;

        cpuOptions.forEach(cpu => {
            const cpuPower = parseInt(cpu.dataset.power) || 0;
            const powerDiff = Math.abs(cpuPower - gpuPower);

            if (powerDiff <= 50) {
                cpu.classList.remove('disabled');
            } else {
                cpu.classList.add('disabled');
            }
        });
    }

    /**
     * Фильтрация материнских плат на основе выбранного процессора
     * Показывает только материнские платы с подходящим сокетом
     */
    function filterMother() {
        if (!selectedCPU) return;

        const motherboardOptions = document.querySelectorAll('.component-option[data-component="motherboard"]');
        const cpuSocket = selectedCPU.socket;

        motherboardOptions.forEach(motherboard => {
            const motherboardSocket = motherboard.dataset.socket;
            if (motherboardSocket === cpuSocket) {
                motherboard.classList.remove('disabled');
            } else {
                motherboard.classList.add('disabled');
            }
        });
    }

    /**
     * Фильтрация оперативной памяти на основе выбранной материнской платы
     * Показывает только модули RAM с подходящим типом
     */
    function filterRAM() {
        if (!selectedMotherboard) return;

        const ramOptions = document.querySelectorAll('.component-option[data-component="ram"]');
        const motherboardRamType = selectedMotherboard.ramType;

        ramOptions.forEach(ram => {
            const ramType = ram.dataset.type;
            if (ramType === motherboardRamType) {
                ram.classList.remove('disabled');
            } else {
                ram.classList.add('disabled');
            }
        });
    }

    /**
     * Фильтрация систем охлаждения на основе выбранной материнской платы
     * Показывает только системы охлаждения с подходящим сокетом
     */
    function filterCooling() {
        if (!selectedMotherboard) return;

        const coolingOptions = document.querySelectorAll('.component-option[data-component="cooling"]');
        const motherboardSocket = selectedMotherboard.socket;

        coolingOptions.forEach(cooling => {
            const coolingSocket = cooling.dataset.socket;
            if (coolingSocket === motherboardSocket) {
                cooling.classList.remove('disabled');
            } else {
                cooling.classList.add('disabled');
            }
        });
    }

    /**
     * Фильтрация блоков питания на основе выбранной видеокарты
     * Показывает только блоки питания с достаточной мощностью
     */
    function filterPSU() {
        if (!selectedGPU) return;

        const psuOptions = document.querySelectorAll('.component-option[data-component="psu"]');
        const gpuConsumption = selectedGPU.consumption;

        psuOptions.forEach(psu => {
            const psuPower = parseInt(psu.dataset.power) || 0;
            if (psuPower >= gpuConsumption) {
                psu.classList.remove('disabled');
            } else {
                psu.classList.add('disabled');
            }
        });
    }

    /**
     * Фильтрация накопителей на основе выбранной материнской платы
     * Показывает только накопители, совместимые с доступными слотами
     */
    function filterStorage() {
        if (!selectedMotherboard) return;

        const storageOptions = document.querySelectorAll('.component-option[data-component="storage"]');
        const sataSlots = selectedMotherboard.sataSlots;

        storageOptions.forEach(storage => {
            const storageType = storage.dataset.type;
            if (storageType.contains('SATA') && sataSlots > 0) {
                storage.classList.remove('disabled');
            } else {
                storage.classList.add('disabled');
            }
        });
    }

    /**
     * Фильтрация корпусов на основе выбранных компонентов
     * Показывает только корпуса, которые:
     * 1. Поддерживают форм-фактор материнской платы
     * 2. Имеют достаточный размер для видеокарты
     */
    function filterCase() {
        if (!selectedMotherboard || !selectedGPU) return;

        const caseOptions = document.querySelectorAll('.component-option[data-component="case"]');
        const motherboardFormFactor = selectedMotherboard.formFactor;
        const gpuSize = parseInt(selectedGPU.size.split('x')[0]) || 0;

        caseOptions.forEach(case_ => {
            const caseFormFactors = case_.dataset.formFactor.split(',').map(f => f.trim());
            const caseSize = parseInt(case_.dataset.size.split(' ')[0]) || 0;
            
            const formFactorMatch = caseFormFactors.includes(motherboardFormFactor);
            const sizeMatch = caseSize >= gpuSize * 1.1; // 10% больше длины видеокарты

            if (formFactorMatch && sizeMatch) {
                case_.classList.remove('disabled');
            } else {
                case_.classList.add('disabled');
            }
        });
    }

    /**
     * Разблокировка следующей категории компонентов
     * Удаляет класс locked со всех компонентов в указанной категории
     */
    function unlockNextCategory(category) {
        const categoryElement = document.querySelector(`.component-option[data-component="${category}"]`).closest('.component-category');
        categoryElement.querySelectorAll('.component-option').forEach(option => {
            option.classList.remove('locked');
        });
    }

    /**
     * Обработка изображений для улучшения качества
     * 1. Создает canvas с увеличенным размером
     * 2. Применяет улучшения качества
     * 3. Конвертирует обратно в изображение
     */
    function processImage(img) {
        img.onload = function() {
            const scale = 5; // Увеличиваем размер для лучшего качества
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d', { 
                alpha: true,
                willReadFrequently: true
            });
            
            canvas.width = img.naturalWidth * scale;
            canvas.height = img.naturalHeight * scale;
            
            ctx.imageSmoothingEnabled = true;
            ctx.imageSmoothingQuality = 'high';
            
            ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
            
            const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
            const data = imageData.data;
            
            // Обработка пикселей временно отключена
            /*
            for (let i = 0; i < data.length; i += 4) {
                const r = data[i];
                const g = data[i + 1];
                const b = data[i + 2];
                
                if (r > 250 && g > 250 && b > 250) {
                    data[i + 3] = 0;
                } else {
                    data[i] = Math.min(255, r * 1.15);
                    data[i + 1] = Math.min(255, g * 1.15);
                    data[i + 2] = Math.min(255, b * 1.15);
                }
            }
            */
            
            ctx.putImageData(imageData, 0, 0);
            img.src = canvas.toDataURL('image/png', 1.5);
        };

        img.onerror = function() {
            console.error('Ошибка загрузки изображения');
            this.src = '/static/images/no-image.png';
        };
    }

    /**
     * Отображение превью выбранного компонента
     * 1. Загружает данные компонента с сервера
     * 2. Отображает изображение и информацию
     * 3. Обрабатывает изображение для улучшения качества
     * 4. Обновляет спецификации и цену
     */
    function showComponentPreview(type, id, name, price) {
        const preview = document.getElementById('component-preview');
        const noSelection = document.getElementById('no-component-selected');
        const previewImage = document.getElementById('preview-image');
        const previewName = document.getElementById('preview-name');
        const previewSpecs = document.getElementById('preview-specs');
        const previewPrice = document.getElementById('preview-price');
        const addButton = document.getElementById('add-to-config');

        noSelection.style.display = 'none';
        preview.style.display = 'block';

        fetch(`/api/component/${type}/${id}/`)
            .then(response => response.json())
            .then(data => {
                if (data.picture) {
                    if (data.picture.startsWith('https')) {
                        previewImage.src = data.picture;
                        previewImage.onload = function() {
                            processImage(this);
                        };
                        previewImage.onerror = function() {
                            console.error('Ошибка загрузки изображения:', data.picture);
                            this.src = '/static/images/no-image.png';
                        };
                    }
                } else {
                    previewImage.src = '/static/images/no-image.png';
                }

                previewName.textContent = data.model;

                // Формирование спецификаций в зависимости от типа компонента
                let specs = '';
                switch (type) {
                    case 'gpu':
                        specs = `Тактовая частота: ${data.frequency || 'Н/Д'}, Объем памяти: ${data.memory_amount || 'Н/Д'} ГБ`;
                        break;
                    case 'cpu':
                        specs = `Ядер: ${data.cores_amount}, Тактовая частота: ${data.frequency}, Сокет: ${data.socket}`;
                        break;
                    case 'motherboard':
                        specs = `Сокет: ${data.socket}, Форм-фактор: ${data.form_factor}`;
                        break;
                    case 'ram':
                        specs = `Суммарный объем памяти: ${data.amount}, Количество модулей: ${data.modules}, Тип ОЗУ: ${data.typee}`;
                        break;
                    case 'cooling':
                        specs = `Тип охлаждения: ${data.typee}, Поддерживаемые сокеты: ${data.socket}`;
                        break;
                    case 'psu':
                        specs = `Номинальная мощность: ${data.power} Вт`;
                        break;
                    case 'storage':
                        specs = `Объем памяти: ${data.capacity}, Тип ПЗУ: ${data.typee}`;
                        break;
                    case 'case':
                        specs = `Поддерживаемые форм-факторы: ${data.supported_form_factor}, Габариты: ${data.size}`;
                        break;
                }
                previewSpecs.textContent = specs;
                previewPrice.textContent = `${price.toLocaleString('ru-RU')} ₽`;

                // Обработчик добавления компонента в конфигурацию
                addButton.onclick = function () {
                    const specElement = document.getElementById(`${type}-spec`);
                    if (specElement) {
                        specElement.textContent = name;
                    }

                    // Сворачиваем категорию выбранного компонента
                    const categoryContent = document.querySelector(`.component-option[data-component="${type}"][data-id="${id}"]`).closest('.category-content');
                    if (categoryContent) {
                        categoryContent.classList.remove('expanded');
                        categoryContent.style.maxHeight = '0';
                        const icon = categoryContent.previousElementSibling.querySelector('i');
                        if (icon) {
                            icon.classList.remove('rotated');
                        }
                    }

                    updatePrice();

                    preview.style.display = 'none';
                    noSelection.style.display = 'block';
                };
            })
            .catch(error => {
                console.error('Ошибка при загрузке данных компонента:', error);
                preview.style.display = 'none';
                noSelection.style.display = 'block';
            });
    }

    /**
     * Обновление общей стоимости конфигурации
     * 1. Суммирует цены всех выбранных компонентов
     * 2. Добавляет стоимость сборки
     * 3. Обновляет отображение цен
     */
    function updatePrice() {
        let total = 0;

        document.querySelectorAll('.component-option.active').forEach(option => {
            const priceText = option.querySelector('.component-price').textContent;
            const price = parseInt(priceText.replace(/[^\d]/g, ''));
            total += price;
        });

        document.getElementById('components-price').textContent = `${total.toLocaleString('ru-RU')} ₽`;

        const assemblyPrice = 4990;
        total += assemblyPrice;

        document.getElementById('total-price').textContent = `${total.toLocaleString('ru-RU')} ₽`;
    }
});