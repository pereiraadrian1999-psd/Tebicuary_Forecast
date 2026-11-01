# %% [markdown]
# ## 7. Ablación: ¿qué ventana de lluvia aporta más?
#
# Se entrena LightGBM con el mismo pipeline cambiando solo el conjunto de variables:
# - `Q`: solo variables de caudal (el modelo aprende la curva de recesión).
# - `Q+Pk`: caudal + lluvia acumulada de *k* días.
# - `Q+todas`: caudal + todas las variables de lluvia.

# %%
conjuntos = {'Q': QCOLS, **{f'Q+P{k}': QCOLS + [f'P{k}'] for k in VENT}, 'Q+todas': QCOLS + PCOLS}
filas = []
for h in HORIZ:
    _, _, ite = datos_h(h)
    for nombre, cols in conjuntos.items():
        pipe = entrenar(h, lgbm(), cols + ['mes'])
        m, _ = evaluar(h, pipe, ite)
        filas.append(dict(h=h, conjunto=nombre, **m))
abl = pd.DataFrame(filas)
orden = list(conjuntos)
tab_skill = abl.pivot(index='conjunto', columns='h', values='Skill_pers').loc[orden]
tab_alto = abl.pivot(index='conjunto', columns='h', values='RMSE_alto').loc[orden]
print('Skill vs persistencia (test):'); print(tab_skill.round(3))
print('\nRMSE en caudales altos, m³/s (test):'); print(tab_alto.round(0))

# %%
fig, ax = plt.subplots(figsize=(7, 4))
im = ax.imshow(tab_skill.values, cmap='Blues', aspect='auto', vmin=0.3, vmax=0.6)
ax.set_xticks(range(len(HORIZ))); ax.set_xticklabels([f'h={h}' for h in HORIZ])
ax.set_yticks(range(len(orden))); ax.set_yticklabels(orden); ax.grid(False)
for i in range(len(orden)):
    for j in range(len(HORIZ)):
        v = tab_skill.values[i, j]
        ax.text(j, i, f'{v:.2f}', ha='center', va='center', fontsize=8, color='white' if v > 0.5 else '#0b0b0b')
ax.set_title('Skill vs persistencia según ventana de lluvia y horizonte', loc='left')
plt.colorbar(im, ax=ax, fraction=0.03)
plt.tight_layout(); plt.savefig(f'{FIG}/ablacion_ventanas.png', dpi=150); plt.show()

# %%
ganancia = (tab_skill.drop(index='Q') - tab_skill.loc['Q'])
print('Ganancia de skill por agregar lluvia respecto al modelo solo-caudal:')
print(ganancia.round(3))
mejor = ganancia.drop(index='Q+todas').idxmax()
print('\nMejor ventana individual por horizonte:', mejor.to_dict())
