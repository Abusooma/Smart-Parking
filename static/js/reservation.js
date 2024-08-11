$(document).ready(function() {
    function updatePrice() {
        var dateArrive = $('#id_date_arrive').val();
        var dateSortie = $('#id_date_sortie').val();

        if (dateArrive && dateSortie) {
            $.ajax({
                url: calculatePriceUrl,  // Utilise l'URL définie dans le template
                data: {
                    'parking_id': parkingId,
                    'date_arrive': dateArrive,
                    'date_sortie': dateSortie
                },
                dataType: 'json',
                success: function(data) {
                    $('#price-display').text(data.price.toFixed(2));
                    $('#duration-display').text(data.duration);
                }
            });
        }
    }

    $('#id_date_arrive, #id_date_sortie').on('change', updatePrice);
});