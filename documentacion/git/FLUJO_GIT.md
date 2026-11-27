# Flujo de Git

> Repositorio: `https://github.com/AmauriGC/Navidad`

## 1. Ramas

```
   main      <- versión estable (la que se entrega o se enseña)
    │  (se sube desde test cuando ya se probó)
   test      <- versión para probar (playtest, build)
    │  (se sube desde develop cuando develop está estable)
   develop   <- rama de trabajo: aquí van todos los commits
```

Regla: el trabajo entra a `develop` y sube `develop -> test -> main`, nunca al revés.

- Es un proyecto de una sola persona: se trabaja **directo en `develop`**, sin ramas
  de trabajo (`feat/...`). Si algún día colabora alguien más, se usan ramas cortas
  desde `develop` y Pull Request.
- `test` y `main` no reciben commits directos; solo merges desde la rama de abajo.

## 2. Trabajo diario

```bash
git switch develop
git pull
# ... cambios ...
git status
git add <rutas del cambio>
git commit -m "tipo(alcance): descripción"
git push
```

## 3. Promover una versión

```bash
git switch test && git pull && git merge --ff-only develop && git push
git switch main && git pull && git merge --ff-only test && git push
git switch develop
```

Antes de promover a `test`: el juego abre sin errores en consola y el build de Linux
compila. Antes de promover a `main`: se jugó una partida completa en el build.
