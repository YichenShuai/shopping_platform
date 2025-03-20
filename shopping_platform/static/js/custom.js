// custom.js
$(document).ready(function() {
    // Product List:
    $('#search-query').on('input', function() {
        var query = $(this).val().toLowerCase();
        $.ajax({
            url: window.location.href,
            method: 'GET',
            success: function() {
                $('.product-item').each(function() {
                    var productName = $(this).data('name');
                    if (productName.includes(query)) {
                        $(this).show();
                    } else {
                        $(this).hide();
                    }
                });
            },
            error: function(xhr) {
                console.log('Filtering failed');
            }
        });
    });

    // Product List:
    $('#search-form').on('submit', function(e) {
        //
    });

    // Manage Inventory & Create Product:
    $('#images').on('change', function(event) {
        const preview = $('#image-preview');
        preview.html('');
        const files = event.target.files;
        for (let i = 0; i < files.length; i++) {
            const file = files[i];
            if (file) {
                const img = $('<img>').attr('src', URL.createObjectURL(file)).css({ maxHeight: '100px', objectFit: 'cover' });
                preview.append(img);
            }
        }
    });

    // Cart:
    $('.update-cart').on('click', function() {
        var itemId = $(this).data('item-id');
        var quantity = $(this).siblings('.quantity-input').val();
        var price = $(this).closest('tr').find('.price').data('price');
        var subtotal = quantity * price;

        $.ajax({
            url: window.location.href,
            method: 'POST',
            data: { quantity: quantity },
            success: function() {
                $('#subtotal-' + itemId).text('$' + subtotal.toFixed(2));
                var total = 0;
                $('.subtotal').each(function() {
                    total += parseFloat($(this).text().replace('$', ''));
                });
                $('#total').text('$' + total.toFixed(2));
            }
        });
    });
});