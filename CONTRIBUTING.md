### Pull Requests (Merge Requests)

So gehst du vor, um Änderungen einzureichen:

1. Wechsle in den `main`-Branch und hole den aktuellen Stand:
   ```bash
   git checkout main
   git pull origin main
   ```

2. Erstelle einen neuen Feature-Branch:
   ```bash
   git checkout -b feature/mein-feature
   ```

3. Führe deine Änderungen durch, committe sie und pushe:
   ```bash
   git add .
   git commit -m "Beschreibe deine Änderung"
   git push origin feature/mein-feature
   ```

4. Gehe zu GitHub und erstelle einen Pull Request gegen `main`.

5. Lasse den Pull Request ggf. überprüfen und merge ihn anschließend.

## Code-Richtlinien

- Schreibe sauberen, nachvollziehbaren Code
- Achte auf klare Commit-Nachrichten
- Wenn möglich: verwende englische Bezeichner

---
