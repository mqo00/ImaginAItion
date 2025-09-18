# From Prompts to Reflection: Designing Reflective Play for GenAI Literacy [(Arxiv)](https://arxiv.org/abs/2509.13679)

![An example sequence from ImaginAItion gameplay](study_material/gameplay.png)

The real game could be played at: [ImaginAItion game online](http://34.162.31.148/) (you'll need to provide your own API key, and 6 rounds of gameplay with the `gpt-image-1` API cost approximately $5). 
Video demo of a game round is available here: https://youtu.be/lwJjuG_eiyc

**Content Directory**
```
├── README.md
├── study_material
│   ├── agg_game_logs.csv
│   ├── prompt_pool
│   │   ├── original_images
│   │   └── original_prompts.csv
│   └── G{1-10}
│       ├── raw_log.json
│       └── images/
└── system
    ├── README.md
    └── ...
```

## study_material: 
`agg_game_logs.csv`: aggregated logs of participants' prompts, votes, scores, etc.

`original_prompts.csv`: original prompts that we used to generate the original images shown to participants during the study.

## system:
`README.md`: instructions for setting up the game system.

## Citation:
Qianou Ma, Megan Chai, Yike Tan, Jihun Choi, Jini Kim, Erik Harpstead, Geoff Kauffman, and Tongshuang Wu. 2025. From Prompts to Reflection: Designing Reflective Play for GenAI Literacy.
```
@misc{ma2025promptsreflectiondesigningreflective,
      title={From Prompts to Reflection: Designing Reflective Play for GenAI Literacy}, 
      author={Qianou Ma and Megan Chai and Yike Tan and Jihun Choi and Jini Kim and Erik Harpstead and Geoff Kauffman and Tongshuang Wu},
      year={2025},
      eprint={2509.13679},
      archivePrefix={arXiv},
      primaryClass={cs.HC},
      url={https://arxiv.org/abs/2509.13679}, 
}
```