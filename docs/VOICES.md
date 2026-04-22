# Voice Reference

54 voices across 9 languages, powered by [Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M). Quality grades from Kokoro's upstream evaluation (A = best, F = lowest).

## American English (11F, 9M)

| Voice ID | Name | Gender | Grade |
|----------|------|--------|-------|
| af_heart | Heart | Female | A |
| af_bella | Bella | Female | A- |
| af_nicole | Nicole | Female | B- |
| af_kore | Kore | Female | C+ |
| af_aoede | Aoede | Female | C+ |
| af_sarah | Sarah | Female | C+ |
| af_alloy | Alloy | Female | C |
| af_nova | Nova | Female | C |
| af_sky | Sky | Female | C- |
| af_jessica | Jessica | Female | D |
| af_river | River | Female | D |
| am_fenrir | Fenrir | Male | C+ |
| am_michael | Michael | Male | C+ |
| am_puck | Puck | Male | C+ |
| am_echo | Echo | Male | D |
| am_eric | Eric | Male | D |
| am_liam | Liam | Male | D |
| am_onyx | Onyx | Male | D |
| am_santa | Santa | Male | D- |
| am_adam | Adam | Male | F+ |

## British English (4F, 4M)

| Voice ID | Name | Gender | Grade | Note |
|----------|------|--------|-------|------|
| bf_emma | Emma | Female | B- | |
| bf_isabella | Isabella | Female | C | |
| bf_alice | Alice | Female | D | |
| bf_lily | Lily | Female | D | |
| bm_fable | Fable | Male | C | **default** |
| bm_george | George | Male | C | |
| bm_lewis | Lewis | Male | D+ | |
| bm_daniel | Daniel | Male | D | |

## Japanese (4F, 1M)

| Voice ID | Name | Gender | Grade |
|----------|------|--------|-------|
| jf_alpha | Alpha | Female | C+ |
| jf_gongitsune | Gongitsune | Female | C |
| jf_tebukuro | Tebukuro | Female | C |
| jf_nezumi | Nezumi | Female | C- |
| jm_kumo | Kumo | Male | C- |

## Mandarin Chinese (4F, 4M)

| Voice ID | Name | Gender | Grade |
|----------|------|--------|-------|
| zf_xiaobei | Xiaobei | Female | D |
| zf_xiaoni | Xiaoni | Female | D |
| zf_xiaoxiao | Xiaoxiao | Female | D |
| zf_xiaoyi | Xiaoyi | Female | D |
| zm_yunjian | Yunjian | Male | D |
| zm_yunxi | Yunxi | Male | D |
| zm_yunxia | Yunxia | Male | D |
| zm_yunyang | Yunyang | Male | D |

## Spanish (1F, 2M)

| Voice ID | Name | Gender | Grade |
|----------|------|--------|-------|
| ef_dora | Dora | Female | -- |
| em_alex | Alex | Male | -- |
| em_santa | Santa | Male | -- |

## French (1F)

| Voice ID | Name | Gender | Grade |
|----------|------|--------|-------|
| ff_siwis | Siwis | Female | B- |

## Hindi (2F, 2M)

| Voice ID | Name | Gender | Grade |
|----------|------|--------|-------|
| hf_alpha | Alpha | Female | C |
| hf_beta | Beta | Female | C |
| hm_omega | Omega | Male | C |
| hm_psi | Psi | Male | C |

## Italian (1F, 1M)

| Voice ID | Name | Gender | Grade |
|----------|------|--------|-------|
| if_sara | Sara | Female | C |
| im_nicola | Nicola | Male | C |

## Brazilian Portuguese (1F, 2M)

| Voice ID | Name | Gender | Grade |
|----------|------|--------|-------|
| pf_dora | Dora | Female | -- |
| pm_alex | Alex | Male | -- |
| pm_santa | Santa | Male | -- |

## Grade Scale

Grades are assigned by the Kokoro model authors based on training data quality and output evaluation.

| Grade | Meaning |
|-------|---------|
| A | Excellent — flagship quality |
| B | Good — reliable for production use |
| C | Decent — usable, some artifacts |
| D | Fair — noticeable quality gaps |
| F | Low — limited training data |
| -- | Not yet graded by upstream |

Grades reflect the Kokoro v1.0 model. See [Kokoro-82M VOICES.md](https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md) for upstream details and audio samples.
