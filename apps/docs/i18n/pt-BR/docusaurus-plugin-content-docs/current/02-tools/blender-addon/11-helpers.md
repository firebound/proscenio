# Auxiliares

Auxiliares de autoria na viewport que preparam o Blender para o trabalho de recorte 2D. Nenhum deles toca no `.proscenio`; eles só mudam como a cena parece enquanto você a autora, então o painel inteiro é **blender-only**. Ele fica por último na barra lateral e vem recolhido por padrão. O painel atualmente contém uma única ferramenta, a Preview Camera.

**Preview Camera** cria uma câmera frontal ortográfica enquadrada do jeito que o importador do Godot espera, para que o que você vê na viewport combine com o enquadramento em tempo de execução. A câmera é nomeada `Proscenio.PreviewCam`: o primeiro clique a adiciona, olhando para baixo em -Y na direção do plano de imagem Y=0, e cada clique posterior refoca e redimensiona a existente em vez de gerar uma segunda câmera.

Sua escala ortográfica é derivada da cena, não adivinhada: o lado mais longo da resolução de render dividido pelo pixels-per-unit da cena (a mesma razão que o subpainel [Exportação](10-pipeline.md#export) define). Isso amarra a extensão visível da câmera à conversão de exportação, então uma figura que preenche o quadro aqui preenche o quadro no Godot. Reexecutar depois de você mudar a resolução de render ou o pixels-per-unit atualiza a escala para combinar.

O operador torna a preview camera a câmera da cena e a seleciona. Pressione <kbd>Numpad 0</kbd> para olhar através dela. É desfazível com <kbd>Ctrl+Z</kbd>.
