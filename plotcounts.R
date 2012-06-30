# plotcounts.R
# Simple R script to plot a date versus count line plot
# Author: Matt Jones, NCEAS< UC Santa Barbara

# Load data from CSV
DT <- format(Sys.time(), "%Y-%m-%d")
cntdata <- read.csv("plotcounts.csv", header = 1, sep = '|')
xdate <- as.Date(cntdata$day)

# Plot the data
graphfile <- paste("plotcounts-dataone-by-date-", DT, ".png", sep="")
png(file=graphfile, height=600, width=600)
par(bg = "white", cex=1.5)
plot(xdate, cntdata$count, ann=FALSE, type="n")
usr <- par("usr")
lines(xdate, cntdata$count, col = "black")
points(xdate, cntdata$count, pch = 20, bg = "lightcyan", cex = 1.5)
title(xlab = "Date", col.lab = "black")
title(ylab = "Cumulative count of data sets", col.lab = "black")
