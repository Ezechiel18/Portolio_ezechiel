CREATE TABLE Proprietaire(
   Code_proprietaire VARCHAR(10),
   Nom VARCHAR(20),
   Type VARCHAR(50),
   Contact INT,
   Numéro_voie VARCHAR(20),
   Nom_de_voie VARCHAR(20),
   Code_postale VARCHAR(20),
   PRIMARY KEY(Code_proprietaire)
);

CREATE TABLE Site_prélèvement(
   Code_site VARCHAR(50),
   Nom_site VARCHAR(50),
   Surface_site DECIMAL(15,2),
   Polygone TEXT,
   Altitude TEXT,
   Pente_pourcentage VARCHAR(50),
   Code_proprietaire VARCHAR(10) NOT NULL,
   PRIMARY KEY(Code_site),
   FOREIGN KEY(Code_proprietaire) REFERENCES Proprietaire(Code_proprietaire)
);

CREATE TABLE Gestionnaire(
   Code_gestionnaire VARCHAR(10),
   Type_gestionnaire VARCHAR(50),
   Contact_gestionnaire INT,
   PRIMARY KEY(Code_gestionnaire)
);

CREATE TABLE Salarié_Ceres(
   Code_salarie VARCHAR(50),
   Nom_salarie VARCHAR(20),
   Prenom_salarie VARCHAR(20),
   Contact_salarie VARCHAR(50),
   PRIMARY KEY(Code_salarie)
);

CREATE TABLE Station(
   Code_station VARCHAR(50),
   Nom_station VARCHAR(20),
   Type_milieu VARCHAR(50),
   Surface DECIMAL(15,2),
   PRIMARY KEY(Code_station)
);

CREATE TABLE Parking(
   Id_parking VARCHAR(10),
   Nom_parking VARCHAR(20),
   Capacite INT,
   Statut VARCHAR(50),
   PRIMARY KEY(Id_parking)
);

CREATE TABLE Espece(
   code_espece VARCHAR(10),
   Nom_scientifique VARCHAR(20) NOT NULL,
   Nom_vernaculaire VARCHAR(20),
   Phenologie VARCHAR(50),
   PRIMARY KEY(code_espece)
);

CREATE TABLE Temperature_moy_annuel(
   Id_temperature VARCHAR(10),
   Valeur DECIMAL(15,2),
   Unite VARCHAR(50),
   Année DATE,
   Code_station VARCHAR(50) NOT NULL,
   PRIMARY KEY(Id_temperature),
   FOREIGN KEY(Code_station) REFERENCES Station(Code_station)
);

CREATE TABLE Pluviométrie_moy_annuel(
   Id_pluviometrie VARCHAR(10),
   Valeur DECIMAL(15,2),
   Unité VARCHAR(50),
   Année DATE,
   Code_station VARCHAR(50) NOT NULL,
   PRIMARY KEY(Id_pluviometrie),
   FOREIGN KEY(Code_station) REFERENCES Station(Code_station)
);

CREATE TABLE EUNIS(
   Code_EUNIS VARCHAR(10),
   Description VARCHAR(50),
   Nom_EUNIS VARCHAR(50),
   Niveau_EUNIS VARCHAR(1),
   PRIMARY KEY(Code_EUNIS)
);

CREATE TABLE Region(
   Id_region VARCHAR(50),
   Nom_region VARCHAR(50),
   Code_INSEE_REG VARCHAR(20),
   PRIMARY KEY(Id_region)
);

CREATE TABLE ZNIEFF(
   Id_ZNIEFF VARCHAR(50),
   Nom VARCHAR(50),
   PRIMARY KEY(Id_ZNIEFF)
);

CREATE TABLE Site_Natura_2000(
   Id__Natura_2000 VARCHAR(50),
   Nom VARCHAR(50),
   PRIMARY KEY(Id__Natura_2000)
);

CREATE TABLE Site_RAMSAR(
   Id_RAMSAR VARCHAR(50),
   Nom_RAMSAR VARCHAR(50),
   Latitude TEXT,
   PRIMARY KEY(Id_RAMSAR)
);

CREATE TABLE Type_de_sol(
   Id_sol VARCHAR(50),
   Nom VARCHAR(50),
   Categorie VARCHAR(50),
   PRIMARY KEY(Id_sol)
);

CREATE TABLE Jeune_plant(
   Code_plant VARCHAR(50),
   Date_germination DATE,
   Taille INT,
   PRIMARY KEY(Code_plant)
);

CREATE TABLE Pépinieriste_Fournisseur(
   Code_fournisseur VARCHAR(50),
   Nom_fournisseur VARCHAR(50),
   Adresse_num_voie VARCHAR(50),
   Adresse_nom_voie VARCHAR(50),
   Complement_adresse VARCHAR(50),
   Code_postale VARCHAR(50),
   Email VARCHAR(50),
   Téléphone VARCHAR(50),
   PRIMARY KEY(Code_fournisseur)
);

CREATE TABLE Lot_de_plant(
   Num_lot VARCHAR(50),
   Nb_plant VARCHAR(50),
   PRIMARY KEY(Num_lot)
);

CREATE TABLE Parcelle_autorisée(
   Id_parcelle VARCHAR(50),
   surface_parcelle DECIMAL(15,2),
   Altitude DECIMAL(15,2),
   PRIMARY KEY(Id_parcelle)
);

CREATE TABLE Autorisation(
   num_autorisation VARCHAR(50),
   PRIMARY KEY(num_autorisation)
);

CREATE TABLE Commande(
   num_commande VARCHAR(50),
   PRIMARY KEY(num_commande)
);

CREATE TABLE Mode_de_livraison(
   num_mode VARCHAR(50),
   Type_livraison VARCHAR(50),
   PRIMARY KEY(num_mode)
);

CREATE TABLE Client(
   Code_client VARCHAR(50),
   Nom_client VARCHAR(50),
   Ad_num_voie VARCHAR(50),
   Ad_type_voie VARCHAR(50),
   Ad_libellé_voie VARCHAR(50),
   Code_postale VARCHAR(50),
   Ville VARCHAR(50),
   Téléphone VARCHAR(50),
   Adr_e_mail VARCHAR(50),
   PRIMARY KEY(Code_client)
);

CREATE TABLE Collectivite_territoriale(
   Code_collectivite VARCHAR(50),
   Forme_juridique VARCHAR(50),
   SIRET VARCHAR(50),
   Effectif INT,
   Code_client VARCHAR(50) NOT NULL,
   PRIMARY KEY(Code_collectivite),
   UNIQUE(Code_client),
   FOREIGN KEY(Code_client) REFERENCES Client(Code_client)
);

CREATE TABLE Bureau_d_etude(
   Code_be VARCHAR(50),
   Forme_juridique VARCHAR(50),
   SIRET VARCHAR(50),
   Effectif INT,
   Responsable VARCHAR(50),
   Code_client VARCHAR(50) NOT NULL,
   PRIMARY KEY(Code_be),
   UNIQUE(Code_client),
   FOREIGN KEY(Code_client) REFERENCES Client(Code_client)
);

CREATE TABLE Particulier(
   Code_pépiniériste VARCHAR(50),
   Code_client VARCHAR(50) NOT NULL,
   PRIMARY KEY(Code_pépiniériste),
   UNIQUE(Code_client),
   FOREIGN KEY(Code_client) REFERENCES Client(Code_client)
);

CREATE TABLE Individu(
   Code_individu VARCHAR(10),
   Nom_individu VARCHAR(20),
   Latitude TEXT,
   Longitude TEXT,
   Altitude TEXT,
   Photo VARCHAR(10),
   code_espece VARCHAR(10) NOT NULL,
   PRIMARY KEY(Code_individu),
   FOREIGN KEY(code_espece) REFERENCES Espece(code_espece)
);

CREATE TABLE Commune(
   Code_INSEE VARCHAR(50),
   Nom_commune VARCHAR(50),
   Code_departement VARCHAR(50),
   Superficie_commune DECIMAL(15,2),
   Id_region VARCHAR(50) NOT NULL,
   PRIMARY KEY(Code_INSEE),
   FOREIGN KEY(Id_region) REFERENCES Region(Id_region)
);

CREATE TABLE Chantier(
   Code_chantier VARCHAR(50),
   Nom_chantier VARCHAR(20),
   Date_debut DATE,
   Date_fin_prevu DATE,
   Date_fin_reelle DATE,
   Type_plantation VARBINARY(20),
   Nbre_de_plants INT,
   Nbre_de_personne_impliquée INT,
   Surface DECIMAL(15,2),
   Statut VARCHAR(20),
   Cout_de_mise_en_oeuvre CURRENCY,
   Photo VARCHAR(20),
   Latitude TEXT,
   Longitude TEXT,
   Altitude TEXT,
   Code_INSEE VARCHAR(50) NOT NULL,
   PRIMARY KEY(Code_chantier),
   FOREIGN KEY(Code_INSEE) REFERENCES Commune(Code_INSEE)
);

CREATE TABLE Individu_prélevé(
   Code_individu_prelev VARCHAR(10),
   branche_nombre INT,
   bouture_nombre INT,
   ramille_nombre INT,
   Code_individu VARCHAR(10) NOT NULL,
   PRIMARY KEY(Code_individu_prelev),
   UNIQUE(Code_individu),
   FOREIGN KEY(Code_individu) REFERENCES Individu(Code_individu)
);

CREATE TABLE Individu_identifié(
   id_individu_identifié VARCHAR(50),
   diametre INT,
   hauteur INT,
   Code_individu VARCHAR(10) NOT NULL,
   PRIMARY KEY(id_individu_identifié),
   UNIQUE(Code_individu),
   FOREIGN KEY(Code_individu) REFERENCES Individu(Code_individu)
);

CREATE TABLE Pole_production(
   Id_pole VARCHAR(50),
   Nom_pole VARCHAR(50),
   Adresse_num_voie_prod VARCHAR(50),
   Adresse_type_voie_prod VARCHAR(50),
   Adresse_libellé_voie_prod VARCHAR(50),
   Adresse_complement_prod VARCHAR(50),
   code_postale_prod VARCHAR(50),
   Code_plant VARCHAR(50) NOT NULL,
   PRIMARY KEY(Id_pole),
   FOREIGN KEY(Code_plant) REFERENCES Jeune_plant(Code_plant)
);

CREATE TABLE Pépiniériste_éleveur(
   Code_pépiniériste VARCHAR(50),
   Code_client VARCHAR(50) NOT NULL,
   PRIMARY KEY(Code_pépiniériste),
   UNIQUE(Code_client),
   FOREIGN KEY(Code_client) REFERENCES Client(Code_client)
);

CREATE TABLE Paysagiste(
   Code_paysagiste VARCHAR(50),
   Forme_juridique VARCHAR(50),
   SIRET VARCHAR(50),
   Effectif INT,
   Dirigeant VARCHAR(50),
   Code_client VARCHAR(50) NOT NULL,
   PRIMARY KEY(Code_paysagiste),
   UNIQUE(Code_client),
   FOREIGN KEY(Code_client) REFERENCES Client(Code_client)
);

CREATE TABLE Gérer(
   Code_site VARCHAR(50),
   Code_gestionnaire VARCHAR(10),
   PRIMARY KEY(Code_site, Code_gestionnaire),
   FOREIGN KEY(Code_site) REFERENCES Site_prélèvement(Code_site),
   FOREIGN KEY(Code_gestionnaire) REFERENCES Gestionnaire(Code_gestionnaire)
);

CREATE TABLE Localise_dans(
   Code_site VARCHAR(50),
   Code_INSEE VARCHAR(50),
   PRIMARY KEY(Code_site, Code_INSEE),
   FOREIGN KEY(Code_site) REFERENCES Site_prélèvement(Code_site),
   FOREIGN KEY(Code_INSEE) REFERENCES Commune(Code_INSEE)
);

CREATE TABLE prospecter(
   Code_site VARCHAR(50),
   Code_salarie VARCHAR(50),
   Date_site_prp DATE,
   PRIMARY KEY(Code_site, Code_salarie),
   FOREIGN KEY(Code_site) REFERENCES Site_prélèvement(Code_site),
   FOREIGN KEY(Code_salarie) REFERENCES Salarié_Ceres(Code_salarie)
);

CREATE TABLE Contenir(
   Code_site VARCHAR(50),
   Code_station VARCHAR(50),
   PRIMARY KEY(Code_site, Code_station),
   FOREIGN KEY(Code_site) REFERENCES Site_prélèvement(Code_site),
   FOREIGN KEY(Code_station) REFERENCES Station(Code_station)
);

CREATE TABLE Prélever(
   Code_salarie VARCHAR(50),
   Code_individu_prelev VARCHAR(10),
   Date_preleve DATE,
   PRIMARY KEY(Code_salarie, Code_individu_prelev),
   FOREIGN KEY(Code_salarie) REFERENCES Salarié_Ceres(Code_salarie),
   FOREIGN KEY(Code_individu_prelev) REFERENCES Individu_prélevé(Code_individu_prelev)
);

CREATE TABLE Incluire(
   Code_site VARCHAR(50),
   Id_parking VARCHAR(10),
   PRIMARY KEY(Code_site, Id_parking),
   FOREIGN KEY(Code_site) REFERENCES Site_prélèvement(Code_site),
   FOREIGN KEY(Id_parking) REFERENCES Parking(Id_parking)
);

CREATE TABLE identifier(
   Code_salarie VARCHAR(50),
   id_individu_identifié VARCHAR(50),
   PRIMARY KEY(Code_salarie, id_individu_identifié),
   FOREIGN KEY(Code_salarie) REFERENCES Salarié_Ceres(Code_salarie),
   FOREIGN KEY(id_individu_identifié) REFERENCES Individu_identifié(id_individu_identifié)
);

CREATE TABLE décrire(
   Code_station VARCHAR(50),
   Code_EUNIS VARCHAR(10),
   PRIMARY KEY(Code_station, Code_EUNIS),
   FOREIGN KEY(Code_station) REFERENCES Station(Code_station),
   FOREIGN KEY(Code_EUNIS) REFERENCES EUNIS(Code_EUNIS)
);

CREATE TABLE Caractériser(
   Code_station VARCHAR(50),
   Id_ZNIEFF VARCHAR(50),
   PRIMARY KEY(Code_station, Id_ZNIEFF),
   FOREIGN KEY(Code_station) REFERENCES Station(Code_station),
   FOREIGN KEY(Id_ZNIEFF) REFERENCES ZNIEFF(Id_ZNIEFF)
);

CREATE TABLE Rattacher(
   Code_station VARCHAR(50),
   Id__Natura_2000 VARCHAR(50),
   PRIMARY KEY(Code_station, Id__Natura_2000),
   FOREIGN KEY(Code_station) REFERENCES Station(Code_station),
   FOREIGN KEY(Id__Natura_2000) REFERENCES Site_Natura_2000(Id__Natura_2000)
);

CREATE TABLE Relever_de(
   Code_station VARCHAR(50),
   Id_RAMSAR VARCHAR(50),
   PRIMARY KEY(Code_station, Id_RAMSAR),
   FOREIGN KEY(Code_station) REFERENCES Station(Code_station),
   FOREIGN KEY(Id_RAMSAR) REFERENCES Site_RAMSAR(Id_RAMSAR)
);

CREATE TABLE est_preleve_dans(
   Code_individu_prelev VARCHAR(10),
   Id_parcelle VARCHAR(50),
   date_prelevement DATE,
   PRIMARY KEY(Code_individu_prelev, Id_parcelle),
   FOREIGN KEY(Code_individu_prelev) REFERENCES Individu_prélevé(Code_individu_prelev),
   FOREIGN KEY(Id_parcelle) REFERENCES Parcelle_autorisée(Id_parcelle)
);

CREATE TABLE Repérer(
   id_individu_identifié VARCHAR(50),
   Id_parcelle VARCHAR(50),
   date_identification DATE,
   PRIMARY KEY(id_individu_identifié, Id_parcelle),
   FOREIGN KEY(id_individu_identifié) REFERENCES Individu_identifié(id_individu_identifié),
   FOREIGN KEY(Id_parcelle) REFERENCES Parcelle_autorisée(Id_parcelle)
);

CREATE TABLE Associer(
   Code_station VARCHAR(50),
   Id_sol VARCHAR(50),
   PRIMARY KEY(Code_station, Id_sol),
   FOREIGN KEY(Code_station) REFERENCES Station(Code_station),
   FOREIGN KEY(Id_sol) REFERENCES Type_de_sol(Id_sol)
);

CREATE TABLE Convoyer(
   Code_individu_prelev VARCHAR(10),
   Id_pole VARCHAR(50),
   _Date DATE,
   Quantité INT,
   PRIMARY KEY(Code_individu_prelev, Id_pole),
   FOREIGN KEY(Code_individu_prelev) REFERENCES Individu_prélevé(Code_individu_prelev),
   FOREIGN KEY(Id_pole) REFERENCES Pole_production(Id_pole)
);

CREATE TABLE Fournir(
   Code_plant VARCHAR(50),
   Code_fournisseur VARCHAR(50),
   _Date DATE,
   Quantité VARCHAR(50),
   PRIMARY KEY(Code_plant, Code_fournisseur),
   FOREIGN KEY(Code_plant) REFERENCES Jeune_plant(Code_plant),
   FOREIGN KEY(Code_fournisseur) REFERENCES Pépinieriste_Fournisseur(Code_fournisseur)
);

CREATE TABLE Fait_partie(
   Code_plant VARCHAR(50),
   Num_lot VARCHAR(50),
   PRIMARY KEY(Code_plant, Num_lot),
   FOREIGN KEY(Code_plant) REFERENCES Jeune_plant(Code_plant),
   FOREIGN KEY(Num_lot) REFERENCES Lot_de_plant(Num_lot)
);

CREATE TABLE Renfermer(
   Code_site VARCHAR(50),
   Id_parcelle VARCHAR(50),
   PRIMARY KEY(Code_site, Id_parcelle),
   FOREIGN KEY(Code_site) REFERENCES Site_prélèvement(Code_site),
   FOREIGN KEY(Id_parcelle) REFERENCES Parcelle_autorisée(Id_parcelle)
);

CREATE TABLE signer(
   Code_proprietaire VARCHAR(10),
   num_autorisation VARCHAR(50),
   Date_demande DATE,
   Date_validation DATE,
   Date_expiration DATE,
   PRIMARY KEY(Code_proprietaire, num_autorisation),
   FOREIGN KEY(Code_proprietaire) REFERENCES Proprietaire(Code_proprietaire),
   FOREIGN KEY(num_autorisation) REFERENCES Autorisation(num_autorisation)
);

CREATE TABLE Concerner(
   Id_parcelle VARCHAR(50),
   num_autorisation VARCHAR(50),
   PRIMARY KEY(Id_parcelle, num_autorisation),
   FOREIGN KEY(Id_parcelle) REFERENCES Parcelle_autorisée(Id_parcelle),
   FOREIGN KEY(num_autorisation) REFERENCES Autorisation(num_autorisation)
);

CREATE TABLE Passer(
   num_commande VARCHAR(50),
   Code_client VARCHAR(50),
   _date DATE,
   Prix VARCHAR(50),
   quantite VARCHAR(50),
   PRIMARY KEY(num_commande, Code_client),
   FOREIGN KEY(num_commande) REFERENCES Commande(num_commande),
   FOREIGN KEY(Code_client) REFERENCES Client(Code_client)
);

CREATE TABLE lier(
   Code_chantier VARCHAR(50),
   num_commande VARCHAR(50),
   PRIMARY KEY(Code_chantier, num_commande),
   FOREIGN KEY(Code_chantier) REFERENCES Chantier(Code_chantier),
   FOREIGN KEY(num_commande) REFERENCES Commande(num_commande)
);

CREATE TABLE Inclure(
   Num_lot VARCHAR(50),
   num_commande VARCHAR(50),
   _Date DATE,
   qté VARCHAR(50),
   prix INT,
   PRIMARY KEY(Num_lot, num_commande),
   FOREIGN KEY(Num_lot) REFERENCES Lot_de_plant(Num_lot),
   FOREIGN KEY(num_commande) REFERENCES Commande(num_commande)
);

CREATE TABLE Livrer(
   num_commande VARCHAR(50),
   num_mode VARCHAR(50),
   _Date DATE,
   Statut_commande VARCHAR(50),
   PRIMARY KEY(num_commande, num_mode),
   FOREIGN KEY(num_commande) REFERENCES Commande(num_commande),
   FOREIGN KEY(num_mode) REFERENCES Mode_de_livraison(num_mode)
);

CREATE TABLE Suit(
   Code_salarie VARCHAR(50),
   Code_chantier VARCHAR(50),
   Date_suivi DATE,
   Etat_sanitaire VARCHAR(50),
   Taux_de_survie VARCHAR(50),
   Commentaire VARCHAR(50),
   PRIMARY KEY(Code_salarie, Code_chantier),
   FOREIGN KEY(Code_salarie) REFERENCES Salarié_Ceres(Code_salarie),
   FOREIGN KEY(Code_chantier) REFERENCES Chantier(Code_chantier)
);
