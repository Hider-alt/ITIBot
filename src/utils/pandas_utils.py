def reformat_csv(path, df):
    """
    It takes a dataframe and writes it to a csv file elaborating the correct format

    :param path: the output path
    :param df: the dataframe to be reformatted
    """
    with open(path, 'w') as f:
        # Headers
        f.write("Ora,Aula,Classe,Doc.Assente,Sostituto 1,Sostituto 2,Note\n")

        # Rows
        for i in range(1, len(df.index), 3):
            row = df.iloc[i]
            aula = df.iloc[i + 1]['Classe'].replace('(', '').replace(')', '')
            classe = df.iloc[i - 1]['Classe']

            f.write(
                row['Ora'] + "," +
                aula + "," +
                classe + "," +
                row['Doc.Assente'] + "," +
                row['Sost.1'] + "," +
                row['Sost.2'] + "," +
                row['Note'] + "\n"
            )