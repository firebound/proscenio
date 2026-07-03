# Atlas

Compõe as imagens de origem da cena em um único atlas compartilhado, reescreve as UVs para endereçá-lo e restaura os originais sob demanda. O empacotamento é opcional - pule-o e cada elemento mantém sua própria textura - então esta é uma etapa de otimização antes da exportação, não um estágio obrigatório. Ele fica em oitavo na barra lateral e vem recolhido por padrão.

O painel abre com uma leitura da textura vinculada nos materiais da cena, rotulada `packed atlas:` quando é a folha compartilhada deste `.blend` ou `source image:` quando é uma origem descoberta. Abaixo dela fica o pixels-per-unit atual, somente leitura aqui porque o subpainel [Exportação](10-pipeline.md#export) é dono do campo editável. Sem textura encontrada, a leitura mostra `no atlas linked in materials`.

A caixa **Atlas packer** contém as configurações de empacotamento e os três operadores. As configurações são campos de cena, salvos com o `.blend`:

- `Pack padding` - pixels de espaçamento reservados em torno de cada célula na folha empacotada. Padrão 2, limitado a 0-64.
- `Pack max size` - um teto rígido nas dimensões da folha empacotada em pixels; o empacotamento falha em vez de excedê-lo. Padrão 4096, limitado a 64-8192.
- `Power-of-two atlas` - arredonda as dimensões empacotadas para cima até uma potência de dois (uma otimização de GPU legada). Desligado por padrão.

Os três operadores exigem o Modo de Objeto, porque os dados de UV de uma malha ficam atrás do BMesh enquanto se está no Modo de Edição.

**Pack Atlas** percorre toda malha de elemento que tem uma imagem de origem, roda o empacotamento MaxRects (best-short-side-fit) no espaçamento e teto configurados, e escreve `<blend>.atlas.png` mais `<blend>.atlas.json` ao lado do `.blend`. É não-destrutivo: UVs e materiais ficam intocados, então é seguro reexecutar enquanto se ajustam as configurações. Uma malha marcada com `Exclude from atlas` fica totalmente fora da varredura; se os sprites não couberem no teto, o empacotamento reporta a falha e não escreve nada.

**Apply Packed Atlas** lê o manifesto e reescreve as UVs de cada elemento do espaço da imagem de origem para o seu lugar na folha empacotada, depois vincula o elemento ao material compartilhado `Proscenio.PackedAtlas`. Um elemento sprite também tem sua região de textura trocada para manual, apontando para o seu lugar. O botão permanece desabilitado até que exista um manifesto empacotado ao lado do `.blend`. Antes de reescrever qualquer coisa, o Apply tira um instantâneo do estado pré-aplicação de cada elemento (suas UVs originais como uma camada de UV duplicada, mais seu material e região de textura) para que o Unpack possa restaurá-lo. Reexecutar o Apply restaura a partir daquele instantâneo primeiro, para que uma segunda aplicação não encolha o lugar ao reempacotar UVs já empacotadas. O operador é desfazível - <kbd>Ctrl+Z</kbd> o reverte - e ele reporta quantos elementos reescreveu e quantos pulou.

**Unpack Atlas** reverte uma aplicação anterior a partir do instantâneo, restaurando as UVs, o material e a região de textura originais de cada elemento. Ele só aparece depois que uma aplicação rodou. Diferente do <kbd>Ctrl+Z</kbd> do Apply, o instantâneo vive no `.blend`, então o Unpack ainda funciona depois de salvar e recarregar. Se um material original foi apagado entre a aplicação e o desempacotamento, as UVs daquele elemento ainda são restauradas e o material faltante é reportado.

**Mantendo um elemento fora da folha compartilhada.** Duas flags por elemento no subpainel [Malha Ativa](02-element.md#active-mesh) controlam como um elemento se relaciona com o atlas. `Isolated material` mantém o elemento no seu próprio shader enquanto ainda desenha pixels da folha empacotada; `Exclude from atlas` o mantém totalmente fora do empacotamento, então ele retém suas próprias UVs, textura e material.

Um elemento de sprite-frame empacotado ainda fatia corretamente. Suas UVs de quad cobrem a folha inteira, então o empacotador mantém aquela folha como um bloco e o Godot subdivide o bloco por `hframes` e `vframes`.
