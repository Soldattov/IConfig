// Конфигуратор ПК
document.addEventListener('DOMContentLoaded', function () {
    // Переменные для хранения выбранных компонентов
    let selectedGPU = null;
    let selectedCPU = null;
    let selectedMotherboard = null;

    // Обработчик раскрытия/сворачивания категорий компонентов
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

    // Обработчик выбора компонентов
    document.querySelectorAll('.component-option').forEach(option => {
        option.addEventListener('click', function () {
            if (this.classList.contains('locked') || this.classList.contains('disabled')) {
                return;
            }

            const componentType = this.dataset.component;
            const componentId = this.dataset.id;
            const componentName = this.querySelector('.component-name').textContent;
            const componentPrice = parseInt(this.querySelector('.component-price').textContent);

            this.parentNode.querySelectorAll('.component-option').forEach(el => {
                el.classList.remove('active');
            });

            this.classList.add('active');
            showComponentPreview(componentType, componentId, componentName, componentPrice);

            if (componentType === 'gpu') {
                selectedGPU = {
                    id: componentId,
                    power: parseInt(this.dataset.power) || 0,
                    consumption: parseInt(this.dataset.consumption) || 0,
                    size: parseInt(this.dataset.size) || 0
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

    function filterCase() {
        if (!selectedMotherboard || !selectedGPU) return;

        const caseOptions = document.querySelectorAll('.component-option[data-component="case"]');
        const motherboardFormFactor = selectedMotherboard.formFactor;
        const gpuSize = selectedGPU.size;

        caseOptions.forEach(case_ => {
            const caseFormFactors = case_.dataset.formFactor.split(',').map(f => f.trim());
            const caseSize = parseInt(case_.dataset.size) || 0;
            
            const formFactorMatch = caseFormFactors.includes(motherboardFormFactor);
            const sizeMatch = caseSize >= gpuSize * 1.1; // 10% больше длины видеокарты

            if (formFactorMatch && sizeMatch) {
                case_.classList.remove('disabled');
            } else {
                case_.classList.add('disabled');
            }
        });
    }

    function unlockNextCategory(category) {
        const categoryElement = document.querySelector(`.component-option[data-component="${category}"]`).closest('.component-category');
        categoryElement.querySelectorAll('.component-option').forEach(option => {
            option.classList.remove('locked');
        });
    }

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
                    }
                } else {
                    previewImage.src = '/static/images/no-image.png';
                }

                previewImage.onerror = function () {
                    console.error('Ошибка загрузки изображения:', data.picture);
                    this.src = '/static/images/no-image.png';
                };

                previewName.textContent = data.model;

                let specs = '';
                switch (type) {
                    case 'gpu':
                        specs = `Тактовая частота: ${data.frequency || 'Н/Д'}, Объем памяти: ${data.memory_amount || 'Н/Д'} ГБ`; //
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

    // Инициализация - раскрываем первую категорию (видеокарты)
    const firstCategory = document.querySelector('.category-content');
    const firstIcon = document.querySelector('.category-header i');
    if (firstCategory && firstIcon) {
        firstCategory.classList.add('expanded');
        firstIcon.classList.add('rotated');
        firstCategory.style.maxHeight = firstCategory.scrollHeight + 'px';
    }
});