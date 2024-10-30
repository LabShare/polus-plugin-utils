class: CommandLineTool
cwlVersion: v1.2
inputs:
  inpDir:
    inputBinding:
      prefix: --inpDir
    type: Directory
  mask:
    inputBinding:
      prefix: --mask
    type: string?
  filePattern:
    inputBinding:
      prefix: --filePattern
    type: string?
  outDir:
    inputBinding:
      prefix: --outDir
    type: Directory
  params:
    inputBinding:
      prefix: --params
    type: string?
  temp:
    type: int[]?
    inputBinding:
      prefix: -temp=
      itemSeparator: " "
      separate: false
  preview:
    inputBinding:
      prefix: --preview
    type: boolean?
outputs:
  outDir:
    outputBinding:
      glob: $(inputs.outDir.basename)
    type: Directory
requirements:
  DockerRequirement:
    dockerPull: polusai/rt-cetsa-intensity-extraction-tool:0.2.0-dev0
  InitialWorkDirRequirement:
    listing:
    - entry: $(inputs.outDir)
      writable: true
  InlineJavascriptRequirement: {}
