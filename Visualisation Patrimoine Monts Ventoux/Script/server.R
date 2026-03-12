library(shiny)
library(sf)
library(dplyr)
library(leaflet)
library(plotly)
library(ggplot2)

server <- function(input, output, session) {
  
  # -------------------
  # 🔹 Chargement des données (Chemins relatifs pour la publication)
  # -------------------
  
  patrimoine_complet <- reactive({
    st_read("elements_patrimoniaux_pnr.gpkg", quiet = TRUE) %>% 
      st_transform(4326)
  })
  
  communes_shp <- reactive({
    st_read("communeventoux.gpkg", quiet = TRUE) %>% 
      st_transform(4326)
  })
  
  pnr_shp <- reactive({
    st_read("pnrventoux.gpkg", quiet = TRUE) %>% 
      st_transform(4326)
  })
  
  # -------------------
  # 🔹 Initialisation filtres
  # -------------------
  
  observe({
    req(patrimoine_complet())
    updateSelectInput(session, "commune",
                      choices = sort(unique(patrimoine_complet()$commune)))
  })
  
  observeEvent(input$commune, {
    req(patrimoine_complet())
    types_dispo <- patrimoine_complet() %>%
      filter(commune == input$commune) %>%
      pull(thematiques) %>% unique() %>% sort()
    
    updateSelectInput(session, "type", choices = types_dispo)
  })
  
  observeEvent(input$type, {
    req(patrimoine_complet())
    natures_dispo <- patrimoine_complet() %>%
      filter(commune == input$commune,
             thematiques == input$type) %>%
      pull(naturedeux) %>% unique() %>% sort()
    
    updateSelectInput(session, "nature", choices = natures_dispo)
  })
  
  # -------------------
  # 🔹 Données filtrées
  # -------------------
  
  data_filtre <- reactive({
    req(input$commune, input$type, input$nature, patrimoine_complet())
    patrimoine_complet() %>%
      filter(commune == input$commune,
             thematiques == input$type,
             naturedeux == input$nature)
  })
  
  # -------------------
  # 🔹 Palette
  # -------------------
  
  pal <- reactive({
    req(patrimoine_complet())
    colorFactor("Dark2", patrimoine_complet()$thematiques)
  })
  
  # -------------------
  # 🗺 Carte avec OSM / Google et multi-couches
  # -------------------
  
  output$map <- renderLeaflet({
    req(communes_shp(), pnr_shp(), patrimoine_complet())
    
    leaflet() %>%
      # FONDS
      addProviderTiles("OpenStreetMap", group = "OSM") %>%
      addProviderTiles("Esri.WorldImagery", group = "Google Satellite") %>%
      
      # COMMUNES
      addPolygons(
        data = communes_shp(),
        fillColor = "transparent",
        color = "#333333",
        weight = 1,
        group = "Communes"
      ) %>%
      
      # PNR
      addPolygons(
        data = pnr_shp(),
        fillColor = "transparent",
        color = "#00A65A",
        weight = 3,
        group = "Contour PNR"
      ) %>%
      
      # PATRIMOINES
      addCircleMarkers(
        data = data_filtre(),
        radius = 7,
        color = ~pal()(thematiques),
        fillOpacity = 0.9,
        stroke = FALSE,
        group = "Patrimoines",
        popup = ~paste(
          "<b>Commune :</b>", commune,
          "<br><b>Thématique :</b>", thematiques,
          "<br><b>Nature :</b>", naturedeux
        )
      ) %>%
      
      # CONTROLE DES COUCHES
      addLayersControl(
        baseGroups = c("OSM", "Google Satellite"),
        overlayGroups = c("Communes", "Contour PNR", "Patrimoines"),
        options = layersControlOptions(collapsed = FALSE)
      )
  })
  
  # -------------------
  # 🔄 Mise à jour dynamique des points
  # -------------------
  
  observe({
    req(data_filtre())
    leafletProxy("map") %>%
      clearGroup("Patrimoines") %>%
      addCircleMarkers(
        data = data_filtre(),
        radius = 7,
        color = ~pal()(thematiques),
        fillOpacity = 0.9,
        stroke = FALSE,
        group = "Patrimoines",
        popup = ~paste(
          "<b>Commune :</b>", commune,
          "<br><b>Thématique :</b>", thematiques,
          "<br><b>Nature :</b>", naturedeux
        )
      )
  })
  
  # -------------------
  # 📊 Graphique Plotly
  # -------------------
  
  output$graph <- renderPlotly({
    req(input$commune)
    
    df_graph <- patrimoine_complet() %>%
      filter(commune == input$commune) %>%
      count(thematiques, naturedeux)
    
    p <- ggplot(df_graph,
                aes(x = thematiques,
                    y = n,
                    fill = naturedeux)) +
      geom_col(position = "stack") +
      theme_minimal(base_size = 14) +
      labs(
        title = paste("Répartition patrimoniale -", input$commune),
        x = "Thématique",
        y = "Nombre d’éléments",
        fill = "Nature"
      )
    
    ggplotly(p)
  })
  
}
