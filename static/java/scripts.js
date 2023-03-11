let slideIndex = 1;
showSlides(slideIndex);

function plusSlides(n) {
  showSlides(slideIndex += n);
}

function currentSlide(n) {
  showSlides(slideIndex = n);
}

function showSlides() {
  var i;
  var slides = document.getElementsByClassName("mySlides");
  var dots = document.getElementsByClassName("dot");
  for (i = 0; i < slides.length; i++) {
    slides[i].style.display = "none";  
  }
  slideIndex++;
  if (slideIndex > slides.length) {slideIndex = 1}    
  for (i = 0; i < dots.length; i++) {
    dots[i].className = dots[i].className.replace(" active", "");
  }
  slides[slideIndex-1].style.display = "block";  
  dots[slideIndex-1].className += " active";
  setTimeout(showSlides, 5000); 
}

$(document).ready(function(){
  // Configuration des paramètres pour l'actualisation du chat
  var refreshInterval = 1000; // Actualiser toutes les 1 seconde
  var chatUrl = '/chat';
  var lastMessageId = 0;

  // Fonction pour envoyer un message au serveur
  function sendMessage(message) {
    $.ajax({
      url: chatUrl,
      type: 'POST',
      data: JSON.stringify({'message': message}),
      contentType: 'application/json; charset=utf-8',
      success: function(data) {
        // On ne fait rien car la réception du message est gérée par la récupération de la liste des messages
      }
    });
  }

  // Fonction pour actualiser la liste des messages
  function refreshMessages() {
    $.ajax({
      url: chatUrl + '?last_message_id=' + lastMessageId,
      type: 'GET',
      contentType: 'application/json; charset=utf-8',
      success: function(data) {
        var messages = data.messages;
        for (var i = 0; i < messages.length; i++) {
          var message = messages[i];
          var messageHtml = '<div class="message">' +
                              '<span class="message-sender">' + message.sender + ':</span> ' +
                              '<span class="message-text">' + message.text + '</span>' +
                            '</div>';
          $('#chat-messages').append(messageHtml);
          lastMessageId = message.id;
        }
      }
    });
  }

  // Configuration des actions pour les boutons
  $('#chat-send-button').click(function() {
    var message = $('#chat-message-input').val();
    sendMessage(message);
    $('#chat-message-input').val('');
  });

  $('#chat-message-input').keypress(function(event) {
    if (event.which == 13) {
      var message = $('#chat-message-input').val();
      sendMessage(message);
      $('#chat-message-input').val('');
    }
  });

  // Actualisation régulière de la liste des messages
  setInterval(refreshMessages, refreshInterval);
});
