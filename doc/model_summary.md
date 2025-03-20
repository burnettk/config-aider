# Model Summary

## Costs early 2025

# model: openrouter/openai/o1 # $/1M 84.2%
# model: openrouter/openai/o1-preview # $/1M 79.7%
# model: openrouter/anthropic/claude-3.5-sonnet # $15/1M 84.2%
# model: openrouter/openai/o3-mini # $4.40/1M
# model: openrouter/deepseek/deepseek-r1 # $2.40/1M
# model: openrouter/anthropic/claude-3-haiku # $1.25/1M
# model: openrouter/deepseek/deepseek-chat # $0.89/1M
# model: openrouter/deepseek/deepseek-r1-distill-llama-70b # $0.69/1M
# model: openrouter/openai/gpt-4o # $/1M 72.9%
# model: openrouter/openai/gpt-4o-mini # $0.60/1M 55.6%
# model: openrouter/qwen/qwen-2.5-72b-instruct # $0.40/1M
# model: openrouter/deepseek/deepseek-r1-distill-qwen-32b # $0.18/1M
# model: openrouter/qwen/qwen-2.5-coder-32b-instruct # $0.16/1M 72.9%
# model: openrouter/microsoft/phi-4 # $0.14/1M
# model: openrouter/gryphe/mythomax-l2-13b # $0.065/1M
# model: gemini/gemini-exp-1206 # $0.0/1M 80.5% whole
# model: gemini/gemini-2.0-flash-exp # $0.0/1M 69.9% diff
# model: gemini/gemini-2.0-flash-thinking-exp-01-21 # $0.0/1M
# model: openrouter/google/gemini-2.0-flash-thinking-exp:free # $0.0/1M

## Cost savings advice 2025-03-19

use claude 3.7 sonnet with --copy-paste mode for free (infinite value, but you have to copypaste yourself. claude 3.7 sonnet ranks #1 in coding)
use openrouter's deepseek r1 free model (infinite value, but 200 request/day limit, deepseek ranks #3 in coding)
use a gemini api key with gemini 2.0 pro (2 reqs/minute) and gemini 2.0 flash (15 reqs/minute) (infinite value, gemini 2.0 pro ties for #7 however you only get 2 requests per minute, gemini 2.0 flash ties for #9)
if you are OK with copypasting, use claude 3.7 sonnet and copy paste
but if its a hassle, use litellm balanced over 2 models (openrouter deepseek r1, gemini 2.0 pro, and gemini 2.0 flash)
this way you can use your 200 free deepseek r1 requests, then your 2 requests/minute gemini 2.0 pro, and then finally gemini 2.0 flash if neither work
these are all infinite value
heres a chart showing model strength
Image
3.7 is by far the best, then claude 3.5 and deepseek r1 have a lead over the rest
then the rest are similar
illumine — Today at 6:12 PM
Awesome reply @supastishn🍉🇵🇸 only other tip I've seen on the budget front is you can use Gemini via OpenRouter and in OpenRouter settings you give it your Gemini API key that it uses as a fallback in case you reach the free request limit.
