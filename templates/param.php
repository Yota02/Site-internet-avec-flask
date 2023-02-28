{% extends "base.html" %}
{% block content %}

<div> 
    <h1 class = "param"> 
       Paramètres
    </h1> 
    <br>
    <div class = "block2" > 
        <h2 class="noir-profil-titre "> 
            Profil 
        </h2>
    </div>
    <div class="block">
        <img class = "pp" src="static/img/icone_defaut.png" height="13%" width="13%">
        <div class="marging"> 

            <br>
            <h1 class="noir-profil">
                Pseudo : {{session.pseudo}}
                <br> 
                id : {{session.id}}
                <br>
                mail : {{session.mail}}
                <br>
                date d'inscription : {{session.date}}
                <br>
           </h1>
           
           <br>
           <p class="logout "> 
            <a href="{{ url_for('logout') }}" >
                Se déconnecter
            </a> </p>
            <p class="update "> 
                <a href="{{ url_for('update') }}" >
                Actualisé
            </a> </p>
            <p class="delet "> 
                <a href="{{ url_for('delete') }}" >
                    Supprimé
                </a> 
            </p>
           <br> 
           
        </div>
    
        
    </div>
<?php
    include ("transfert.php");
    if ( isset($_FILES['fic']) )
    {
        transfert();
    }
 ?>
    <div class = "block"> 
        <br>
        <form enctype="multipart/form-data" action="#" method="post">
            <input type="hidden" name="MAX_FILE_SIZE" value="250000" />
            <input type="file" name="fic" size=50 />
            <input type="submit" value="Envoyer" />
         </form>
    </div>

</div>


{% endblock %}

