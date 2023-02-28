<?php
    function transfert(){
        $ret        = false;
        $img_blob   = '';
        $img_taille = 0;
        $img_type   = '';
        $img_nom    = '';
        $taille_max = 250000;
        $ret        = is_uploaded_file($_FILES['fic']['tmp_name']);
        
        if (!$ret) {
            echo "Problème de transfert";
            return false;
        } else {
            // Le fichier a bien été reçu
            $img_taille = $_FILES['fic']['size'];
            
            if ($img_taille > $taille_max) {
                echo "Trop gros !";
                return false;
            }

            $img_type = $_FILES['fic']['type'];
            $img_nom  = $_FILES['fic']['name'];
            include ("connexion.php");
            $img_blob = file_get_contents ($_FILES['fic']['tmp_name']);
            $req = "INSERT INTO images (" .
                            "img_nom, img_taille, img_type, img_blob " .
                            ") VALUES (" .
                            "'" . $img_nom . "', " .
                            "'" . $img_taille . "', " .
                            "'" . $img_type . "', " .
                            "'" . addslashes ($img_blob) . "') "; 
            $ret = mysql_query ($req) or die (mysql_error ());
            return true;
        }
    }
?>