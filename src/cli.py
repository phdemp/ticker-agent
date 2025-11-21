from listener import rank_new_tickers
def main():
    df = rank_new_tickers()
    if df.empty:
        print("No tickers found.")
    else:
        print("Early-ticker rank (last 7 days):")
        print(df.to_string(index=False))
if __name__ == '__main__':
    main()