library(dplyr)
library(sf)
library(concaveman)

files=list.files('../data/')
ii=grep('.geojson',files)
pol=list()
for(i in ii){
    pol[[i]]=concave_polygon(file.path('..','data',files[i]))
}

concave_polygon = function(filename) {
    edges_pts=st_read(filename)  %>% st_transform(32724)
    selected_pts = edges_pts %>% group_by(id) %>% tally %>% filter(n==max(n))
    polygon = selected_pts %>% concaveman(.,concavity=1.5)
    return(polygon)
}
