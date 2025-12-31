
--Déclarer la clé primaire de la table  region
ALTER TABLE region
ADD CONSTRAINT pk_region PRIMARY KEY (idregion);

-- commune → region
--- ajout des clés primaires de région dans commune 
ALTER TABLE commune ADD COLUMN idregion INTEGER;

UPDATE commune c
SET idregion = r.idregion
FROM region r
WHERE ST_Intersects(c.geom, r.geom);
---- add pk chez commune
ALTER TABLE commune
ADD CONSTRAINT pk_commune PRIMARY KEY (idcommune);

---- id region entant que fk chez commune
ALTER TABLE commune ALTER COLUMN idregion SET NOT NULL;
ALTER TABLE commune
ADD CONSTRAINT fk_commune_region
FOREIGN KEY (idregion)
REFERENCES region(idregion);

-------- add idlocalite as pk
ALTER TABLE localite
ADD CONSTRAINT pk_localite PRIMARY KEY (idlocalite);

---- detecter les cooresspondance localité - commune
ALTER TABLE localite ADD COLUMN idcommune INTEGER;

UPDATE localite l
SET idcommune = c.idcommune
FROM commune c
WHERE ST_Within(l.geom, c.geom);

---- idcommune en tant que fk chez localite
ALTER TABLE localite ALTER COLUMN idcommune SET NOT NULL;
ALTER TABLE localite
ADD CONSTRAINT fk_localite_commune
FOREIGN KEY (idcommune)
REFERENCES commune(idcommune);

---- add idap as pk de aire_protege
ALTER TABLE aire_protege
ADD CONSTRAINT pk_ap PRIMARY KEY (idap);

--- ajout de pk  chez la table se_trouver-- subtilité-deux table en clé primaire
ALTER TABLE se_trouver
ADD CONSTRAINT pk_se_trouver
PRIMARY KEY (idap, idlocalite);
-- insertion de la relatoions spatriale afin de remplir les  tables de cls primaires
INSERT INTO se_trouver (idap, idlocalite)
SELECT
    ap.idap,
    l.idlocalite
FROM aire_protege ap
JOIN localite l
ON ST_Contains(ap.geom, l.geom);
-- declaration des foreign key de la table se_trouver
--- les pk chez la table se_trouver etant de type varchar il faut les convertir d'abord en int
ALTER TABLE se_trouver
ALTER COLUMN idap TYPE INTEGER
USING idap::INTEGER;

ALTER TABLE se_trouver
ALTER COLUMN idlocalite TYPE INTEGER
USING idlocalite::INTEGER;

---- vers aire_protege

ALTER TABLE se_trouver
ADD CONSTRAINT fk_se_trouver_aire
FOREIGN KEY (idap)
REFERENCES aire_protege(idap);

----- vers  localite
ALTER TABLE se_trouver
ADD CONSTRAINT fk_se_trouver_localite
FOREIGN KEY (idlocalite)
REFERENCES localite(idlocalite);

--- suite 25/12/2025

---declaration de la clé primair de la table sitearestaurer
ALTER TABLE sitearestaurer
ADD CONSTRAINT pk_site
PRIMARY KEY (idsite);

-- déclaration des clés primaires de la table rattacher
ALTER TABLE rattacher
ADD CONSTRAINT 	pk_rattacher
PRIMARY KEY (idsite, idlocalite);
--- remplir les champs idsite et idlocalite de la table rattacher à l'aide de la  relation spaiale de locaite et siterestayurer
INSERT INTO rattacher (idsite, idlocalite)
SELECT
    s.idsite,
    l.idlocalite
FROM sitearestaurer s
JOIN localite l
ON ST_Contains(s.geom, l.geom);

--- les pk chez la table rattacher etant de type varchar il faut les convertir d'abord en int
ALTER TABLE rattacher
ALTER COLUMN idsite TYPE INTEGER
USING idsite::INTEGER;

ALTER TABLE rattacher
ALTER COLUMN idlocalite TYPE INTEGER
USING idlocalite::INTEGER;

--- declaration des fk de rattacher
-- vers localite
ALTER TABLE rattacher
ADD CONSTRAINT fk_rattacher_localite
FOREIGN KEY (idlocalite)
REFERENCES localite(idlocalite);

---vers sitearestaurer
ALTER TABLE rattacher
ADD CONSTRAINT fk_rattacher_sitearestaurer
FOREIGN KEY (idsite)
REFERENCES sitearestaurer(idsite);

-------- ajout de pk de zoneplantation
ALTER TABLE zoneplantation
ADD CONSTRAINT pk_idzone
PRIMARY KEY (idzone);

---- ajout de idsite dans zoneplanatation
ALTER TABLE zoneplantation ADD COLUMN idsite INTEGER;

UPDATE zoneplantation z
SET idsite = s.idsite
FROM sitearestaurer s
WHERE ST_Within(ST_PointOnSurface(z.geom), s.geom);

------- ajout de la colonne idsite  chez zone planatation en tant que FK 
ALTER TABLE zoneplantation ALTER COLUMN idsite SET NOT NULL;
ALTER TABLE zoneplantation
ADD CONSTRAINT fk_zoneplantation_site
FOREIGN KEY (idsite)
REFERENCES sitearestaurer(idsite);

--- déclaration  de la PK de la table indicateur
ALTER TABLE indicateur
ADD CONSTRAINT pk_indicateur
PRIMARY KEY (idindic);

---- déclaration de la PK de la table baseline
ALTER TABLE baseline
ADD CONSTRAINT pk_baseline
PRIMARY KEY (idbaseline);

--- Déclaration de la FK dz la table baseline vers table indicateur
---- changer le champ idindic de indicateur en INT dans un 1er temps
ALTER TABLE indicateur
ALTER COLUMN idindic TYPE INTEGER
USING idindic::INTEGER;

---- changer le champ idindic de baseline en INT dans un 1er temps
ALTER TABLE baseline
ALTER COLUMN idindic TYPE INTEGER
USING idindic::INTEGER;

-- etape proprement dite
ALTER TABLE baseline ALTER COLUMN idindic SET NOT NULL;
ALTER TABLE baseline
ADD CONSTRAINT fk_baseline_indic
FOREIGN KEY (idindic)
REFERENCES indicateur(idindic);

---- Déclaration de la FK dz la table baseline vers table sitearestaurer
---- changer le champ idsite de baseline en INT dans un 1er temps
ALTER TABLE baseline
ALTER COLUMN idsite TYPE INTEGER
USING idsite::INTEGER;

---- Etape de déclaration proprement dite
ALTER TABLE baseline ALTER COLUMN idsite SET NOT NULL;
ALTER TABLE baseline
ADD CONSTRAINT fk_baseline_site
FOREIGN KEY (idsite)
REFERENCES sitearestaurer(idsite);

---- déclaration de la PK de la table cible
ALTER TABLE cible
ADD CONSTRAINT pk_cible
PRIMARY KEY (idcible);

---- Déclaration de la FK dz la table cible vers table sitearestaurer
---- changer le champ idsite de cible en INT dans un 1er temps
ALTER TABLE cible
ALTER COLUMN idsite TYPE INTEGER
USING idsite::INTEGER;

---- Etape de déclaration proprement dite
ALTER TABLE cible ALTER COLUMN idsite SET NOT NULL;
ALTER TABLE cible
ADD CONSTRAINT fk_cible_site
FOREIGN KEY (idsite)
REFERENCES sitearestaurer(idsite);

---- Déclaration de la FK dz la table cible vers table sitearestaurer
---- changer le champ idindic de cible en INT dans un 1er temps
ALTER TABLE cible
ALTER COLUMN idindic TYPE INTEGER
USING idindic::INTEGER;

---- Etape de déclaration proprement dite
ALTER TABLE cible ALTER COLUMN idindic SET NOT NULL;
ALTER TABLE cible
ADD CONSTRAINT fk_cible_indic
FOREIGN KEY (idindic)
REFERENCES indicateur(idindic);

--- Declaration de la clé primaire de la table typeactivite
---- changer le champ idtacti de cible en INT dans un 1er temps
ALTER TABLE typeactivite
ALTER COLUMN idtacti TYPE INTEGER
USING idtacti::INTEGER;

--- Déclaration proprement dite
ALTER TABLE typeactivite
ADD CONSTRAINT pk_typeactivite
PRIMARY KEY (idtacti)



--- Declaration de la clé primaire de la table acteur
---- changer le champ idtacti de cible en INT dans un 1er temps
ALTER TABLE acteur
ALTER COLUMN idacteur TYPE INTEGER
USING idacteur::INTEGER;

--- Déclaration proprement dite
ALTER TABLE acteur
ADD CONSTRAINT pk_acteur
PRIMARY KEY (idacteur)


--- Déclaration de la PK de réalisation
---- changer le champ idrealisation de realisation en INT dans un 1er temps
ALTER TABLE realisation
ALTER COLUMN idrealisation TYPE INTEGER
USING idrealisation::INTEGER;

--- Déclaration proprement dite
ALTER TABLE realisation
ADD CONSTRAINT pk_realisation
PRIMARY KEY (idrealisation)

-- déclration des  FK de réalisation
-- déclaration de idindic vers table indicateur
---- changer le champ idindic de realisation en INT dans un 1er temps
ALTER TABLE realisation
ALTER COLUMN idindic TYPE INTEGER
USING idindic::INTEGER;

---- Etape de déclaration proprement dite de idindic
ALTER TABLE realisation ALTER COLUMN idindic SET NOT NULL;
ALTER TABLE realisation
ADD CONSTRAINT fk_realisation_indic
FOREIGN KEY (idindic)
REFERENCES indicateur(idindic);

--- declaration vers table zoneplnatation
---- changer le champ idzone de realisation en INT dans un 1er temps
ALTER TABLE realisation
ALTER COLUMN idzone TYPE INTEGER
USING idzone::INTEGER;

-- Etant donné queidzone dans reamisation # de idzone dans zoneplantation
DELETE FROM realisation
WHERE idzone NOT IN (
    SELECT idzone FROM zoneplantation
);

---- Etape de déclaration proprement dite de idindic

ALTER TABLE realisation ALTER COLUMN idzone SET NOT NULL;
ALTER TABLE realisation
ADD CONSTRAINT fk_realisation_idzone
FOREIGN KEY (idzone)
REFERENCES zoneplantation(idzone);

--- declaration vers table typeactivite
---- changer le champ idtacti de realisation en INT dans un 1er temps
ALTER TABLE realisation
ALTER COLUMN idtacti TYPE INTEGER
USING idtacti::INTEGER;

---- Etape de déclaration proprement dite de idindic
ALTER TABLE realisation ALTER COLUMN idtacti SET NOT NULL;
ALTER TABLE realisation
ADD CONSTRAINT fk_realisation_typeacti
FOREIGN KEY (idtacti)
REFERENCES typeactivite(idtacti);

--- declaration des PK de la table effectuer
---- changer les champs idacteur et idrealisation  en INT dans un 1er temps
ALTER TABLE effectuer
ALTER COLUMN idacteur TYPE INTEGER
USING idacteur::INTEGER;

ALTER TABLE effectuer
ALTER COLUMN idrealisation TYPE INTEGER
USING idrealisation::INTEGER;

-- declaration de idrealisation et de idacteur comme clés primaires
ALTER TABLE effectuer
ADD CONSTRAINT pk_effectuer
PRIMARY KEY (idacteur,idrealisation)

--- declaration des FK de la table effectuer
--- vers la table acteur
--- suppression des non coressponsances entre effectuer et acteur
DELETE FROM effectuer
WHERE idacteur NOT IN (
    SELECT idacteur FROM acteur
);
--- declaration  de FKproprement dite

ALTER TABLE effectuer ALTER COLUMN idacteur SET NOT NULL;
ALTER TABLE effectuer
ADD CONSTRAINT fk_effectuer_acteur
FOREIGN KEY (idacteur)
REFERENCES acteur(idacteur);

--- vers la table  realisation
--- suppression des non coressponsances 
DELETE FROM effectuer
WHERE idrealisation NOT IN (
    SELECT idrealisation FROM realisation
);

--FK preoprement dit
ALTER TABLE effectuer ALTER COLUMN idrealisation SET NOT NULL;
ALTER TABLE effectuer
ADD CONSTRAINT fk_effectuer_realisation
FOREIGN KEY (idrealisation)
REFERENCES realisation(idrealisation);


--- declaration de PK la tbale entretien
---- changer le champ identretien de entretien en INT dans un 1er temps
ALTER TABLE entretien
ALTER COLUMN identretien TYPE INTEGER
USING identretien::INTEGER;

---- Etape de déclaration proprement dite de identretien
ALTER TABLE entretien
ADD CONSTRAINT pk_entretien
PRIMARY KEY (identretien)

--FK idtacti preoprement dit
--changer type de idtcti dans entretien
ALTER TABLE entretien
ALTER COLUMN idtacti TYPE INTEGER
USING idtacti::INTEGER;

ALTER TABLE entretien ALTER COLUMN idtacti SET NOT NULL;
ALTER TABLE entretien
ADD CONSTRAINT fk_entretien_typeacti
FOREIGN KEY (idtacti)
REFERENCES typeactivite(idtacti);


--- declaration de PK la table plantation
---- changer le champ identretien de entretien en INT dans un 1er temps
ALTER TABLE plantation
ALTER COLUMN idplantation TYPE INTEGER
USING idplantation::INTEGER;

---- Etape de déclaration proprement dite de identretien
ALTER TABLE plantation
ADD CONSTRAINT pk_plantation
PRIMARY KEY (idplantation)

--FK idtacti preoprement dit chez plantation
--changer type de idtacti dans entretien
ALTER TABLE plantation
ALTER COLUMN idtacti TYPE INTEGER
USING idtacti::INTEGER;

ALTER TABLE plantation ALTER COLUMN idtacti SET NOT NULL;
ALTER TABLE plantation
ADD CONSTRAINT fk_plantation_typeacti
FOREIGN KEY (idtacti)
REFERENCES typeactivite(idtacti);



--- declaration de PK la tbale sensibilisation
---- changer le champ idsens de sensibilisation en INT dans un 1er temps
ALTER TABLE sensibilisation
ALTER COLUMN idsens TYPE INTEGER
USING idsens::INTEGER;

---- Etape de déclaration proprement dite de idsens
ALTER TABLE sensibilisation
ADD CONSTRAINT pk_sensibilisation
PRIMARY KEY (idsens)

--FK idtacti preoprement dit vers typeactivite
--changer type de idtcti dans sensibilisation
ALTER TABLE sensibilisation
ALTER COLUMN idtacti TYPE INTEGER
USING idtacti::INTEGER;

ALTER TABLE sensibilisation ALTER COLUMN idtacti SET NOT NULL;
ALTER TABLE sensibilisation
ADD CONSTRAINT fk_sensibilisation_typeacti
FOREIGN KEY (idtacti)
REFERENCES typeactivite(idtacti);

--FK idlocalite preoprement dit vers localite
--changer type de idlocalite dans sensibilisation
ALTER TABLE sensibilisation
ALTER COLUMN idlocalite TYPE INTEGER
USING idlocalite::INTEGER;

ALTER TABLE sensibilisation ALTER COLUMN idlocalite SET NOT NULL;
ALTER TABLE sensibilisation
ADD CONSTRAINT fk_sensibilisation_localite
FOREIGN KEY (idlocalite)
REFERENCES localite(idlocalite);

--- Declaration de la clé primaire de la table espece
---- changer le champ idespece de espece en INT dans un 1er temps
ALTER TABLE espece
ALTER COLUMN idespece TYPE INTEGER
USING idespece::INTEGER;

--- Déclaration proprement dite
ALTER TABLE espece
ADD CONSTRAINT pk_espece
PRIMARY KEY (idespece)



--- declaration de PK la table utiliser
---- changer les champs id de utiliser en INT dans un 1er temps
ALTER TABLE utiliser
ALTER COLUMN idplantation TYPE INTEGER
USING idplantation::INTEGER;

ALTER TABLE utiliser
ALTER COLUMN idespece TYPE INTEGER
USING idespece::INTEGER;

---- Etape de déclaration proprement dite de PK
ALTER TABLE utiliser
ADD CONSTRAINT pk_utiliser
PRIMARY KEY (idplantation,idespece)

--FK idplantation preoprement dit vers plantation
--changer type de idplantation dans utiliser
ALTER TABLE utiliser
ALTER COLUMN idplantation TYPE INTEGER
USING idplantation::INTEGER;

ALTER TABLE utiliser ALTER COLUMN idplantation SET NOT NULL;
ALTER TABLE utiliser
ADD CONSTRAINT fk_utiliser_plantation
FOREIGN KEY (idplantation)
REFERENCES plantation(idplantation);

--FK idespece preoprement dit vers espece
--changer type de idespece dans utiliser
ALTER TABLE utiliser
ALTER COLUMN idespece TYPE INTEGER
USING idespece::INTEGER;
-- suppression de non correspondance entre idespece de utiiser et idespece de espece
DELETE FROM utiliser
WHERE idespece NOT IN (
    SELECT idespece FROM espece
);
--- FK idespece chez utiliser
ALTER TABLE utiliser ALTER COLUMN idespece SET NOT NULL;
ALTER TABLE utiliser
ADD CONSTRAINT fk_utiliser_espece
FOREIGN KEY (idespece)
REFERENCES espece(idespece);

---- création des index spatiaux sur les couches spatiales uniqument bien evidemment
--sur la couche commune
CREATE INDEX idx_commune_geom
ON commune
USING GIST (geom);

--sur la couche région

CREATE INDEX idx_region_geom
ON region
USING GIST (geom);

--sur la couche zoneplantation

CREATE INDEX idx_zoneplantation_geom
ON zoneplantation
USING GIST (geom);

--sur la couche sitearestaurer

CREATE INDEX idx_sitearestaurer_geom
ON sitearestaurer
USING GIST (geom);

--sur la couche localite

CREATE INDEX idx_localite_geom
ON localite
USING GIST (geom);

--sur la couche aire_protege

CREATE INDEX idx_aire_protege_geom
ON aire_protege
USING GIST (geom);

---  Requête pour identifier les zones de plantation pour 
--lesquelles les réalisations observées sont inférieures aux objectifs définis (cibles)
CREATE VIEW vue_zones_ecart_negatif AS
SELECT 
    z.idzone AS id,
    z.nomzone,
    s.nomsite,
    i.nomindic,
    c.valeur::numeric AS valeur_cible,
    r.valeurealise::numeric AS valeurealise,
    (r.valeurealise::numeric - c.valeur::numeric) AS ecart,
    z.geom
FROM zoneplantation z
JOIN sitearestaurer s ON z.idsite = s.idsite
JOIN realisation r ON z.idzone = r.idzone
JOIN indicateur i ON r.idindic = i.idindic
JOIN cible c ON c.idsite = s.idsite 
            AND c.idindic = i.idindic
            -- Ajoutez ici la condition temporelle si nécessaire
            -- AND c.periode = r.periode
WHERE r.valeurealise::numeric < c.valeur::numeric
  AND r.valeurealise IS NOT NULL
  AND c.valeur IS NOT NULL;
---
SELECT r.valeurealise::numeric, c.valeur::numeric
FROM realisation r
JOIN cible c ON r.idindic = c.idindic;
-----

---Le nombre de réalisations (d'intervention) sur chaque zoneplantation
CREATE VIEW vue_zones_realisation AS
SELECT
    z.idzone AS id,
    s.idsite,
    z.geom,
    z.nomzone,
    COUNT(r.idrealisation) AS nb_realisation,
    SUM(r.valeurealise::numeric) AS total_realise,
    CASE
        WHEN SUM(r.valeurealise::numeric) IS NULL THEN 'Aucune réalisation'
        WHEN SUM(r.valeurealise::numeric) >= 200 AND SUM(r.valeurealise::numeric) < 6000 THEN 'Faible'
		WHEN SUM(r.valeurealise::numeric) >= 6000 AND SUM(r.valeurealise::numeric) < 7000 THEN 'Moyen'
        WHEN SUM(r.valeurealise::numeric) >= 7000 THEN 'Élevé'
    END AS classement_realisation
FROM zoneplantation z
LEFT JOIN realisation r ON z.idzone = r.idzone
JOIN sitearestaurer s ON z.idsite = s.idsite
GROUP BY z.idzone, z.nomzone, s.idsite, z.geom;


------Le nombre de réalisations (d'intervention) sur chaque zoneplantation -- en centroid

CREATE VIEW vue_zones_realisation_centroid AS
SELECT
    z.idzone AS id,
    s.idsite,
    ST_Centroid(z.geom) AS geom,
    z.nomzone,
    COUNT(r.idrealisation) AS nb_realisation,
    SUM(r.valeurealise::numeric) AS total_realise,
    CASE
        WHEN SUM(r.valeurealise::numeric) IS NULL THEN 'Aucune réalisation'
        WHEN SUM(r.valeurealise::numeric) >= 200 AND SUM(r.valeurealise::numeric) < 6000 THEN 'Faible'
        WHEN SUM(r.valeurealise::numeric) >= 6000 AND SUM(r.valeurealise::numeric) < 7000 THEN 'Moyen'
        WHEN SUM(r.valeurealise::numeric) >= 7000 THEN 'Élevé'
    END AS classement_realisation
FROM zoneplantation z
LEFT JOIN realisation r ON z.idzone = r.idzone
JOIN sitearestaurer s ON z.idsite = s.idsite
GROUP BY z.idzone, z.nomzone, s.idsite, z.geom;

