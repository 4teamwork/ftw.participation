/* invitations view select all */
jQuery(function($) {
     $('.select_all_invitations').click(
       function() {
         var parents = $(this).parents('table:first').find('input');
         if ($(this).attr('checked') === false) {
           parents.attr('checked', '');
         }
         else {
           parents.attr('checked', 'checked');
         }
       });

  $('[href*=invite_participants]').prepOverlay(
    {'subtype':'ajax',
     'filter': '#content > *',
     'closeselector': '#form-buttons-button_cancel'});
  });
