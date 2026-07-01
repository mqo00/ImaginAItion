# "GenAI Defaults to Bias!" Gamify AI Literacy Through Reflections on Prompts [(Paper)](https://doi.org/10.1007/978-3-032-29763-1_7)[(Arxiv)](https://arxiv.org/abs/2509.13679)

AIED 2026.
![An example sequence from ImaginAItion gameplay](study_material/gameplay.png)

The real game could be played at: [ImaginAItion game online](http://34.162.31.148/) (you'll need to provide your own API key, and 6 rounds of gameplay with the `gpt-image-1` API cost approximately $5). 
Video demo of a game round is available here: https://youtu.be/lwJjuG_eiyc

**Content Directory**
```
├── README.md
├── study_material
│   ├── supplements.pdf
│   ├── agg_game_logs.csv
│   ├── prompt_pool.csv
│   └── G{1-10}
│       ├── game_log.json
│       └── images/
└── system
    ├── README.md
    ├── backend/static/reference_images/
    └── ...
```

## study_material: 
`supplements.pdf`: supplemental materials to the AIED26 paper, including player group composition, game implementation details, survey questions, etc.


`agg_game_logs.csv`: aggregated logs of participants' prompts, votes, scores, etc.

`prompt_pool.csv`: original prompts that we used to generate the original images shown to participants during the study.

`G{1-10}/game_log.json`: raw game log per group, including generation faillures. 

`G{1-10}/images/`: generated images from participants in the study, downsized for repository upload, named after "img-{round}-{player_id}-{action_type}-{first_three_tokens}"


## system:
`README.md`: instructions for setting up the game system.

`backend/static/reference_images/`: original images used in the game. 


## Citation:
Ma, Q. et al. (2026). “GenAI Defaults to Bias!” Gamify AI Literacy Through Reflections on Prompts. In: Blanchard, E.G., Chen, G., Chi, M., Isotani, S. (eds) Artificial Intelligence in Education. AIED 2026. Lecture Notes in Computer Science, vol 16584. Springer, Cham. https://doi.org/10.1007/978-3-032-29763-1_7


```
@InProceedings{ma2026imaginaition,
    title="``GenAI Defaults to Bias!'' Gamify AI Literacy Through Reflections on Prompts",
    author="Ma, Qianou
        and Chai, Megan
        and Tan, Yike
        and Choi, Jihun
        and Kim, Jini
        and Harpstead, Erik
        and Kauffman, Geoff
        and Wu, Tongshuang",
    editor="Blanchard, Emmanuel G.
        and Chen, Guanliang
        and Chi, Min
        and Isotani, Seiji",
    booktitle="Artificial Intelligence in Education",
    year="2026",
    publisher="Springer Nature Switzerland",
    address="Cham",
    pages="91--106",
    isbn="978-3-032-29763-1"
}
```