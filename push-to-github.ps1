# Script pour pousser vers GitHub

$gitPath = "C:\Program Files\Git\bin\git.exe"

# Configuration Git
& $gitPath config --global user.name "armshivb"
& $gitPath config --global user.email "ashivbar@gmail.com"

# Initialiser le repo
& $gitPath init

# Ajouter les fichiers
& $gitPath add .

# Créer un commit
& $gitPath commit -m "Initial commit - Mariage RSVP site"

# Ajouter la remote
& $gitPath remote add origin https://github.com/armshivb/mariage-melissa-armonde.git

# Pousser vers GitHub
& $gitPath branch -M main
& $gitPath push -u origin main

Write-Host "Push terminé !"
