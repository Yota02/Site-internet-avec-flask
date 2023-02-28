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
<div class = "block"> 
<?php
error_reporting(0);
 
$msg = "";
if (isset($_POST['upload'])) {
    $filename = $_FILES["uploadfile"]["name"];
    $tempname = $_FILES["uploadfile"]["tmp_name"];
    $folder = "./image/" . $filename;
    $db = mysqli_connect("localhost", "root", "", "geeksforgeeks");
    $sql = "INSERT INTO image (filename) VALUES ('$filename')";
    mysqli_query($db, $sql);
}
?>
<div id="content">
        <form method="POST" action="" enctype="multipart/form-data">
            <div class="form-group">
                <input class="form-control" type="file" name="uploadfile" value="" />
            </div>
            <div class="form-group">
                <button class="btn btn-primary" type="submit" name="upload">UPLOAD</button>
            </div>
        </form>
    </div>
</div>
{% endblock %}