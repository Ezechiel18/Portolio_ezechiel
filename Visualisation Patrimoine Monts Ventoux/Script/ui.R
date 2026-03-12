library(shiny)
library(shinydashboard)
library(sf)
library(dplyr)
library(leaflet)
library(plotly)
library(ggplot2)

# -------------------
# UI
# -------------------
ui <- dashboardPage(
  
  skin = "green",
  
  dashboardHeader(title = "PNR Mont-Ventoux"),
  
  dashboardSidebar(
    sidebarMenu(
      menuItem("Filtres", icon = icon("filter")),
      selectInput("commune", "Choisir une commune", choices = NULL),
      selectInput("type", "Choisir une thématique", choices = NULL),
      selectInput("nature", "Choisir une nature", choices = NULL)
    )
  ),
  
  dashboardBody(
    fluidRow(
      box(
        title = "Répartition patrimoniale",
        width = 12,
        status = "success",
        solidHeader = TRUE,
        plotlyOutput("graph", height = 350)
      )
    ),
    fluidRow(
      box(
        title = "Carte interactive",
        width = 12,
        status = "success",
        solidHeader = TRUE,
        leafletOutput("map", height = 600)
      )
    )
  )
)