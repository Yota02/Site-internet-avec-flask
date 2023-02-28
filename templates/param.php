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

require './bdd.php';

if(isset($_FILES['file'])){
    $tmpName = $_FILES['file']['tmp_name'];
    $name = $_FILES['file']['name'];
    $size = $_FILES['file']['size'];
    $error = $_FILES['file']['error'];

    $tabExtension = explode('.', $name);
    $extension = strtolower(end($tabExtension));

    $extensions = ['jpg', 'png', 'jpeg', 'gif'];
    $maxSize = 400000;

    if(in_array($extension, $extensions) && $size <= $maxSize && $error == 0){

        $uniqueName = uniqid('', true);
        
        $file = $uniqueName.".".$extension;

        move_uploaded_file($tmpName, './upload/'.$file);

        $req = $db->prepare('INSERT INTO images (name) VALUES (?)');
        $req->execute([$file]);

        echo "Image enregistrée";
    }
    else{
        echo "Une erreur est survenue";
    }
}

?>
    <div class = "block"> 
        <br>
        <form action="upload.php" method="post" enctype="multipart/form-data">
    Select Image File to Upload:
    <input type="file" name="file">
    <input type="submit" name="submit" value="Upload">
        </form>


    <h2>Mes images</h2>
    <?php
include 'dbConfig.php';

$query = $db->query("SELECT * FROM images ORDER BY uploaded_on DESC");

if($query->num_rows > 0){
    while($row = $query->fetch_assoc()){
        $imageURL = 'uploads/'.$row["file_name"];
?>
    <img src="<?php echo $imageURL; ?>" alt="" />
<?php }
}else{ ?>
    <p>No image(s) found...</p>
<?php } ?>
    </div>

</div>

{% endblock %}

