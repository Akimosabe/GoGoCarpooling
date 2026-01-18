(function() {
    'use strict';
    console.log('trip_seats.js loaded v2');
    
    const MAX_SEATS = 9;
    const MIN_TOTAL_SEATS = 1;
    const MIN_AVAILABLE_SEATS = 0;
    
    document.addEventListener('DOMContentLoaded', function() {
        const totalSeatsInput = document.getElementById('id_total_seats');
        const availableSeatsInput = document.getElementById('id_available_seats');
        
        if (!totalSeatsInput || !availableSeatsInput) {
            return;
        }
        
        // Увеличиваем размер полей
        totalSeatsInput.style.width = '80px';
        availableSeatsInput.style.width = '80px';
        
        // Функция для ограничения значения в поле
        function clampValue(input, min, max) {
            let value = parseInt(input.value);
            if (isNaN(value) || value < min) {
                value = min;
            } else if (value > max) {
                value = max;
            }
            input.value = value;
            return value;
        }
        
        // Обработчик для total_seats - не даёт ввести больше MAX_SEATS
        function handleTotalSeatsInput() {
            const value = clampValue(totalSeatsInput, MIN_TOTAL_SEATS, MAX_SEATS);
            
            // Обновляем максимум для available_seats
            availableSeatsInput.max = value;
            
            // Если available_seats больше нового total_seats, корректируем
            const availableValue = parseInt(availableSeatsInput.value) || 0;
            if (availableValue > value) {
                availableSeatsInput.value = value;
            }
        }
        
        // Обработчик для available_seats - не даёт ввести больше total_seats
        function handleAvailableSeatsInput() {
            const maxAvailable = parseInt(totalSeatsInput.value) || MAX_SEATS;
            clampValue(availableSeatsInput, MIN_AVAILABLE_SEATS, Math.min(maxAvailable, MAX_SEATS));
        }
        
        // Блокируем ввод недопустимых значений при каждом нажатии клавиши
        totalSeatsInput.addEventListener('input', handleTotalSeatsInput);
        totalSeatsInput.addEventListener('change', handleTotalSeatsInput);
        totalSeatsInput.addEventListener('blur', handleTotalSeatsInput);
        
        availableSeatsInput.addEventListener('input', handleAvailableSeatsInput);
        availableSeatsInput.addEventListener('change', handleAvailableSeatsInput);
        availableSeatsInput.addEventListener('blur', handleAvailableSeatsInput);
        
        // Блокируем вставку недопустимых значений
        totalSeatsInput.addEventListener('paste', function(e) {
            setTimeout(handleTotalSeatsInput, 0);
        });
        availableSeatsInput.addEventListener('paste', function(e) {
            setTimeout(handleAvailableSeatsInput, 0);
        });
        
        // Инициализация при загрузке
        if (totalSeatsInput.value) {
            handleTotalSeatsInput();
        }
        if (availableSeatsInput.value) {
            handleAvailableSeatsInput();
        }
    });
})();
