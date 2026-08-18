# Logotipos

`cepal_logo.svg` es el logotipo institucional que la CEPAL publica en su sitio:

    https://www.cepal.org/sites/default/files/2025-02/cepal_logo.svg

`cepal_logo.png` (544 × 668) es ese mismo archivo rasterizado con LibreOffice,
porque Excel no admite SVG. `cepal_marca.png` (242 × 92) es la marca horizontal
sola, sin el emblema de Naciones Unidas:

    https://www.cepal.org/themes/contrib/eclacstrap_base/images/brand/eclac-logo-es.svg

Se guardan en el repositorio a propósito: la generación de los libros no debe
depender de que el sitio esté en línea ni de que la URL siga viva. Para
actualizarlos, bajar el SVG y convertirlo con:

    soffice --headless --convert-to png --outdir assets assets/cepal_logo.svg
